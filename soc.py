from burp import IBurpExtender, ITab, IProxyListener, IHttpService, IContextMenuFactory, IContextMenuInvocation
from javax.swing import JTabbedPane, JPanel, JButton, JTextArea, JScrollPane, JTextField
from java.awt import GridBagLayout, GridBagConstraints
from java.awt.event import ActionListener
import re

class WebSocketMatchReplace(IBurpExtender, ITab, IProxyListener, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("WebSocket Match & Replace")

        # Create a tab for the UI
        self.tab = JTabbedPane()
        self.panel = JPanel()
        self.panel.setLayout(GridBagLayout())
        self._input_area = JTextArea(10, 50)
        self._output_area = JTextArea(10, 50)
        self._match_field = JTextField(50)
        self._replace_field = JTextField(50)
        scroll_pane_input = JScrollPane(self._input_area)
        scroll_pane_output = JScrollPane(self._output_area)
        self._match_button = JButton("Match & Replace", actionPerformed=self.process_match_replace)

        self.panel.add(scroll_pane_input)
        self.panel.add(scroll_pane_output)
        self.panel.add(self._match_field)
        self.panel.add(self._replace_field)
        self.panel.add(self._match_button)

        self.tab.addTab("WebSocket Match & Replace", self.panel)
        callbacks.addSuiteTab(self)

        # Initialize the rules
        self.rules = []

        # Register for WebSocket interception
        callbacks.registerProxyListener(self)

    def getTabCaption(self):
        return "WebSocket Match & Replace"

    def getUiComponent(self):
        return self.tab

    def createMenuItems(self, invocation):
        self.invocation = invocation
        return [WebSocketMenuItem(self)]

    def processProxyMessage(self, messageIsRequest, message):
        if not messageIsRequest:
            # Handle WebSocket response messages
            response_info = self._helpers.analyzeResponse(message.getMessage())
            if response_info.getStatedMimeType() == "WebSocket":

                # Convert the response to bytes
                response_bytes = message.getMessage()[response_info.getBodyOffset():]

                # Modify the response based on defined rules
                modified_response_bytes = self.modifyWebSocketResponse(response_bytes)
                if modified_response_bytes:
                    # Send the modified response back to the client
                    self.sendModifiedResponse(message.getMessageInfo(), modified_response_bytes)

    def modifyWebSocketResponse(self, response_bytes):
        response_str = response_bytes.tostring()
        modified_response_str = response_str

        # Apply matching and replacement rules
        for match, replace in self.rules:
            modified_response_str = re.sub(match, replace, modified_response_str)

        # Create a new response as bytes
        modified_response_bytes = self._helpers.stringToBytes(modified_response_str)

        return modified_response_bytes

    def sendModifiedResponse(self, message_info, modified_response_bytes):
        # Create a Runnable task to send the modified response
        class SendResponseTask(Runnable):
            def run(self):
                self._callbacks.sendToClient(ByteArrayInputStream(modified_response_bytes), message_info)

        # Execute the task in a separate thread
        send_response_task = SendResponseTask()
        threading.Thread(target=send_response_task.run).start()

    def process_match_replace(self, e):
        match_text = self._match_field.getText()
        replace_text = self._replace_field.getText()

        if match_text and replace_text:
            self.rules.append((match_text, replace_text))
            self._match_field.setText("")
            self._replace_field.setText("")

            # Update the UI with the current rules
            self.update_rule_display()

    def update_rule_display(self):
        rule_display = ""
        for match, replace in self.rules:
            rule_display += f"Match: {match}\nReplace: {replace}\n\n"
        self._output_area.text = rule_display

class WebSocketMenuItem(IContextMenuFactory):
    def __init__(self, extender):
        self._extender = extender

    def createMenuItems(self, invocation):
        menu_items = []

        if isinstance(invocation, IContextMenuInvocation):
            menu_items.append(WebSocketContextMenuItem(self._extender))

        return menu_items

class WebSocketContextMenuItem(IContextMenuFactory):
    def __init__(self, extender):
        self._extender = extender

    def createMenuItems(self, invocation):
        return [WebSocketMatchReplaceMenuItem(self._extender)]

class WebSocketMatchReplaceMenuItem(IContextMenuFactory):
    def __init__(self, extender):
        self._extender = extender

    def createMenuItems(self, invocation):
        menu_items = []
        menu_items.append(WebSocketMenuItem(self._extender))
        return menu_items

# Register the extension
WebSocketMatchReplace()
