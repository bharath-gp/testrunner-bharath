from failover.AutoFailoverBaseTest import AutoFailoverBaseTest
from membase.api.exception import RebalanceFailedException, \
    ServerUnavailableException


class AutoFailoverTests(AutoFailoverBaseTest):
    def setUp(self):
        super(AutoFailoverTests, self).setUp()
        self.master = self.servers[0]

    def tearDown(self):
        super(AutoFailoverTests, self).tearDown()

    def test_enable(self):
        self.enable_autofailover()
        settings = self.rest.get_autofailover_settings()
        self.assertTrue(settings.enabled)

    def test_disable(self):
        self.disable_autofailover()
        settings = self.rest.get_autofailover_settings()
        self.assertFalse(settings.enabled)

    def test_autofailover(self):
        self.enable_autofailover_and_validate()
        self.sleep(5)
        self.failover_actions[self.failover_action](self)

    def test_autofailover_during_rebalance(self):
        self.enable_autofailover_and_validate()
        self.sleep(5)
        rebalance_task = self.cluster.async_rebalance(self.servers,
                                                      self.servers_to_add,
                                                      self.servers_to_remove)
        self.sleep(10)
        self.failover_actions[self.failover_action](self)
        try:
            rebalance_task.result()
        except RebalanceFailedException:
            pass
        except ServerUnavailableException:
            pass
        else:
            self.fail("Rebalance should fail since a node went down")

    def test_autofailover_after_rebalance(self):
        self.enable_autofailover_and_validate()
        self.sleep(5)
        rebalance_success = self.cluster.rebalance(self.servers,
                                                   self.servers_to_add,
                                                   self.servers_to_remove)
        if not rebalance_success:
            self.disable_firewall()
            self.fail("Rebalance failed. Check logs")
        self.failover_actions[self.failover_action](self)

    def test_rebalance_after_autofailover(self):
        self.enable_autofailover_and_validate()
        self.sleep(5)
        self.failover_actions[self.failover_action](self)
        for node in self.servers_to_add:
            self.rest.add_node(user=self.orchestrator.rest_username,
                               password=self.orchestrator.rest_password,
                               remoteIp=node.ip)
        nodes = self.rest.node_statuses()
        nodes_to_remove = [node.id for node in nodes if
                           node.ip in [t.ip for t in self.servers_to_remove]]
        nodes = [node.id for node in nodes]
        started = self.rest.rebalance(nodes, nodes_to_remove)
        rebalance_success = False
        if started:
            rebalance_success = self.rest.monitorRebalance()
        if not rebalance_success or not started:
            self.fail("Rebalance failed. Check logs")

    def test_autofailover_and_addback_of_node(self):
        self.enable_autofailover_and_validate()
        self.sleep(5)
        self.failover_actions[self.failover_action](self)
        self.bring_back_failed_nodes_up()
        self.sleep(30)
        self.log.info(self.server_to_fail[0])
        self.nodes = self.rest.node_statuses()
        self.log.info(self.nodes[0].id)
        self.rest.add_back_node("ns_1@{}".format(self.server_to_fail[0].ip))
        self.rest.set_recovery_type("ns_1@{}".format(self.server_to_fail[
                                                         0].ip),
                                    self.recovery_strategy)
        self.rest.rebalance(otpNodes=[node.id for node in self.nodes])
        msg = "rebalance failed while recovering failover nodes {0}".format(
            self.server_to_fail[0])
        self.assertTrue(self.rest.monitorRebalance(stop_if_loop=True), msg)

    def test_autofailover_and_remove_failover_node(self):
        self.enable_autofailover_and_validate()
        self.sleep(5)
        self.failover_actions[self.failover_action](self)
        self.nodes = self.rest.node_statuses()
        self.remove_after_failover = True
        self.rest.rebalance(otpNodes=[node.id for node in self.nodes])
        msg = "rebalance failed while removing failover nodes {0}".format(
            self.server_to_fail[0])
        self.assertTrue(self.rest.monitorRebalance(stop_if_loop=True), msg)
