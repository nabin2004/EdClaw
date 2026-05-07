
class AgentSession:
    def __init__(self, store, session_id):
        self.store = store
        self.session_id = session_id
        self.session = store.get(session_id)

    @property
    def backing(self):
        """Underlying persisted session (gateway-owned)."""
        return self.session

    def add_user_message(self, text):
        self.session.add_user_message(text)

    def add_assistant_message(self, text):
        self.session.add_assistant_message(text)

    @property
    def messages(self):
        return self.session.messages