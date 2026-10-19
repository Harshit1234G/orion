INTENT_DETECTION = [
    {
        'type': 'choice',
        'name': 'intent_detection',
        'instructions': 'Classify the user utterance into exactly one intent based on its meaning and context.',
        'choices': [
            {
                'value': 'wakeword',
                'description': 'User only activates Orion, optionally with a greeting, without asking anything else. Examples: "Orion", "Hey Orion".'
            },
            {
                'value': 'interrupt',
                'description': 'User asks Orion to stop or pause its current response or speech, without necessarily canceling the task. Examples: "Stop talking", "Wait".'
            },
            {
                'value': 'cancel_task',
                'description': 'User explicitly cancels or abandons the current task. Stronger than interrupting speech. Examples: "Cancel that", "Never mind", "Forget that".'
            },
            {
                'value': 'shutdown',
                'description': 'User explicitly asks Orion itself to shut down or exit, not the operating system.'
            },
            {
                'value': 'instruction',
                'description': 'Any meaningful question, request, command, follow-up, or conversational utterance that does not match another intent. Use even if the request is unclear.'
            },
            {
                'value': 'gibberish',
                'description': 'Unintelligible, meaningless, accidental noise, or fragments with no identifiable intent. Do not use for valid but unclear instructions.'
            }
        ]
    }
]