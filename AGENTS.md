# Bubseek Agent Instructions

## DingTalk Channel ($dingtalk)

When the message context shows `$dingtalk` and `chat_id`, you are in a DingTalk conversation.

**To reply: return your response as plain text.** The framework will deliver it to the user. Do not call any script; just write your answer and finish the turn.

Only use `dingtalk_send` when you need to send a message from within a tool (e.g. progress update during a long task).
