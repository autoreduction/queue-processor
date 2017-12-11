/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package isis.autoreducequeuechecker;

import java.util.Collections;
import java.util.List;
import javax.jms.Connection;
import javax.jms.JMSException;
import javax.jms.QueueBrowser;
import javax.jms.Session;
import org.apache.activemq.ActiveMQConnectionFactory;
import org.apache.activemq.command.ActiveMQQueue;

public class QueueChecker {
    
    private static final int OK = 0;
    private static final int WARNING = 1;
    private static final int CRITICAL = 2;
    private static final int UNKNOWN = 3;
    
    public static void main(String[] args) {	
        ActiveMQConnectionFactory connectionFactory = new ActiveMQConnectionFactory("tcp://localhost:61616");

        String username = "autoreduce";
        String password = "activedev";

        connectionFactory.setUserName(username);
        connectionFactory.setPassword(password);

        Connection connection = null;
        
        // Connect to ActiveMQ
        try {
            connection = connectionFactory.createConnection();
            connection.start();
        } catch (JMSException e) {
            e.printStackTrace();
        }
        
        Session session = null;
        List<?> messages = null;
        
        // Connect to the queue given in the program arguments
        try {
            session = connection.createSession(false, 1);
             ActiveMQQueue queueName = new ActiveMQQueue(args[0]);

            QueueBrowser queue = session.createBrowser(queueName);

            messages = Collections.list(queue.getEnumeration());
        } catch (JMSException e) {
            System.out.println(UNKNOWN + " " + e.getMessage());
        }
        
        // Set up the number of messages that would be critical or a warning
        // amount
        int size = messages.size();
        int warningAmount;
        int criticalAmount;
        
        try {
            warningAmount = Integer.parseInt(args[1]);
            criticalAmount = Integer.parseInt(args[2]);
            // Print the output for NAGIOS so it knows what type of message to
            // send to the relevant autoreduce admins
            if (size >= criticalAmount) {
                System.out.println(CRITICAL + " " + args[0] + " size is: " + size);
            } else if ((size >= warningAmount) && (size < criticalAmount)) {
                System.out.println(WARNING + " " + args[0] + " size is: " + size);
            } else {
                System.out.println(OK);
            }
        } catch (Exception e) {
            System.out.println(e + " Incorrect Values parsed.");
        }
        
        try {
            connection.close();
            session.close();
        } catch (JMSException e) {
            e.printStackTrace();
        }
    }
}

