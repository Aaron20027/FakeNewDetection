
class Audit():
    def __init__(self, audit_log_id,performed_by,action,user_agent,ip_address,timestamp):
        self.audit_log_id=audit_log_id
        self.performed_by=performed_by
        self.action=action
        self.user_agent=user_agent
        self.ip_address=ip_address
        self.timestamp=timestamp
  