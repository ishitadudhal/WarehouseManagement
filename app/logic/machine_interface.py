"""
Machine Interface — connects the WMS software to the REAL physical warehouse
(the Hochregallager in the Digitale Fabrik lab) via OPC UA.

This module is written against the ACTUAL, documented OPC UA server structure
of our lab's warehouse, as described in:

    Yannik Ubben, "Integration eines Hochregallagers mittels OPC UA",
    Masterarbeit MII, Hochschule Emden/Leer, 13.04.2025 — Anhang B.

The PLC (Siemens) runs an OPC UA Server built with Siemens SIOME.
Its namespace URI is:  http://TechnikumEID13.hsel.de

Known nodes (from the thesis' Appendix B XML export):

    Lager (Warehouse)
      └─ Funktionen (Functions)
            Einlagern      (Boolean)  — trigger a STORE operation
            Auslagern      (Boolean)  — trigger a RETRIEVE operation
            Umlagern       (Boolean)  — trigger a RELOCATE operation
            Referenzieren  (Boolean)  — send the axes back to their home position
      └─ Steuerung allgemein (General control)
            Hand_Automatik (Boolean)  — Manual / Automatic mode switch
            Steuerung_Ein  (Boolean)  — Master "control enabled" switch
      └─ Sicherheitsfunktionen (Safety functions)
            Not_Aus            (Boolean) — Emergency stop status
            Kollisionen        (Boolean) — Collision detected
            Safety_IO          (Boolean) — General safety IO status
            Wartungstür_offen  (Boolean) — Maintenance door open

NOTE: The exact Node IDs for selecting WHICH shelf (target X, Y, Z) were not
fully captured from the thesis excerpt available to us. Before this module can
actually run against the real machine, someone with lab access needs to either:
  1. Confirm the OPC UA server's IP address / endpoint (opc.tcp://<ip>:4840), and
  2. Browse the live server (e.g. with UaExpert) to find the position/target nodes.

Until then, ENDPOINT_URL below is a placeholder and connect() will simply fail
loudly and clearly rather than pretend to succeed.
"""

# pip install asyncua
import os
from asyncua.sync import Client

# ── Configuration — read from .env, with a placeholder fallback ────────────
# Fill in OPCUA_ENDPOINT_URL in your .env file once the lab gives you the
# real machine's IP address, e.g.:  OPCUA_ENDPOINT_URL=opc.tcp://192.168.1.50:4840
ENDPOINT_URL = os.environ.get("OPCUA_ENDPOINT_URL", "opc.tcp://<PLC-IP-ADDRESS>:4840")
NAMESPACE_URI = "http://TechnikumEID13.hsel.de"

# Node paths, relative to the "Lager" object, as documented in Ubben (2025) Anhang B
NODE_PATHS = {
    "einlagern":       "0:Objects/1:Lager/1:Funktionen/1:Einlagern",
    "auslagern":       "0:Objects/1:Lager/1:Funktionen/1:Auslagern",
    "umlagern":        "0:Objects/1:Lager/1:Funktionen/1:Umlagern",
    "referenzieren":   "0:Objects/1:Lager/1:Funktionen/1:Referenzieren",
    "steuerung_ein":   "0:Objects/1:Lager/1:Steuerung allgemein/1:Steuerung Ein",
    "hand_automatik":  "0:Objects/1:Lager/1:Steuerung allgemein/1:Hand Automatik",
    "not_aus":         "0:Objects/1:Lager/1:Sicherheitsfunktionen/1:Not Aus",
    "kollisionen":     "0:Objects/1:Lager/1:Sicherheitsfunktionen/1:Kollisionen",
}


class MachineInterface:
    """
    Thin wrapper around an OPC UA client, scoped to exactly what our
    Order Manager needs: trigger a store/retrieve, and check safety status.
    """

    def __init__(self, endpoint_url=ENDPOINT_URL):
        self.endpoint_url = endpoint_url
        self.client = None

    def connect(self):
        self.client = Client(self.endpoint_url)
        self.client.connect()

    def disconnect(self):
        if self.client:
            self.client.disconnect()

    def _get_node(self, key):
        path = NODE_PATHS[key]
        return self.client.get_node(path)

    def is_control_enabled(self):
        """Checks the 'Steuerung Ein' (Control Enabled) flag before sending any command."""
        return self._get_node("steuerung_ein").get_value()

    def is_safe(self):
        """Returns False if Emergency Stop is pressed or a collision was detected."""
        not_aus = self._get_node("not_aus").get_value()
        kollision = self._get_node("kollisionen").get_value()
        return not (not_aus or kollision)

    def trigger_store(self):
        """Pulses the 'Einlagern' (Store) trigger on the real machine."""
        if not self.is_safe():
            raise RuntimeError("Machine is not in a safe state (E-Stop or collision).")
        self._get_node("einlagern").set_value(True)

    def trigger_retrieve(self):
        """Pulses the 'Auslagern' (Retrieve) trigger on the real machine."""
        if not self.is_safe():
            raise RuntimeError("Machine is not in a safe state (E-Stop or collision).")
        self._get_node("auslagern").set_value(True)


# ── Quick manual test ────────────────────────────────────────────────────────
# Run this file directly (after filling in ENDPOINT_URL) to sanity-check the
# connection without going through the whole Flask app:
#
#   python app/logic/machine_interface.py
#
if __name__ == "__main__":
    mi = MachineInterface()
    mi.connect()
    print("Connected. Control enabled:", mi.is_control_enabled())
    mi.disconnect()
