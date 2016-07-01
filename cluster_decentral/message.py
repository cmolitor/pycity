__author__ = 'Sonja Kolen'

class Message(object):
    def __init__(self, Sender_ID, Receiver_ID, type, data):
        """
        constructor of Message class
        :param Sender_ID: ID of sender CommBes object
                Sender_ID=0 indicates a message from the cluster administration ("system message")
        :param Receiver_ID: ID of receiver CommBes object
        :param type: Type of message
            type = 0 indicates a "system message" coming from cluster administration
            type = 20 indicates a pseudo tree generation message
            type = 40 indicates a load propagation OPT message
            type = 70 indicates a remainder multicast optimization message

        :param msgdata: data of message
        :return:
        """
        self.IDSender = Sender_ID
        self.IDReceiver = Receiver_ID
        self.msgType = type
        self.msgdata = data

    def getIDSender(self):
        return self.IDSender

    def getIDReceiver(self):
        return self.IDReceiver

    def getType(self):
        return self.msgType

    def getData(self):
        return self.msgdata