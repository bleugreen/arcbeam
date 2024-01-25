from dataclasses import dataclass
import json

@dataclass
class ButtonEvent:
    button_name: str
    event_type: str
    duration: float = 0.0

    def __str__(self):
        return json.dumps({
            "button_name": self.button_name,
            "event_type": self.event_type,
            "duration": self.duration
        })

    @classmethod
    def from_string(cls, string):
        data = json.loads(string)
        return cls(
            button_name=data["button_name"],
            event_type=data["event_type"],
            duration=data.get("duration", 0.0)
        )
