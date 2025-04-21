import requests
import xml.etree.ElementTree as ET

DEVICE_IP = "10.29.60.78"
PORT = 60006
CONTROL_URL = f"http://{DEVICE_IP}:{PORT}/upnp/control/renderer_dvc/AVTransport"
HEADERS = {
    "Content-Type": 'text/xml; charset="utf-8"',
}

def build_soap_envelope(action, service, body_xml):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
            s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:{action} xmlns:u="{service}">
      {body_xml}
    </u:{action}>
  </s:Body>
</s:Envelope>"""

def send_upnp_action(action, body_xml, service="urn:schemas-upnp-org:service:AVTransport:1"):
    headers = HEADERS.copy()
    headers["SOAPACTION"] = f'"{service}#{action}"'
    envelope = build_soap_envelope(action, service, body_xml)
    response = requests.post(CONTROL_URL, data=envelope, headers=headers)
    return response.text

def get_transport_info():
    print("🛰 Getting Transport Info...")
    xml = send_upnp_action("GetTransportInfo", "<InstanceID>0</InstanceID>")
    print(xml)

def play():
    print("▶️ Sending Play command...")
    xml = send_upnp_action("Play", "<InstanceID>0</InstanceID><Speed>1</Speed>")
    print(xml)

def pause():
    print("⏸ Sending Pause command...")
    xml = send_upnp_action("Pause", "<InstanceID>0</InstanceID>")
    print(xml)

def stop():
    print("⏹ Sending Stop command...")
    xml = send_upnp_action("Stop", "<InstanceID>0</InstanceID>")
    print(xml)

def set_uri(uri):
    print(f"🔗 Setting URI to: {uri}")
    xml_body = f"""
    <InstanceID>0</InstanceID>
    <CurrentURI>{uri}</CurrentURI>
    <CurrentURIMetaData></CurrentURIMetaData>
    """
    xml = send_upnp_action("SetAVTransportURI", xml_body)
    print(xml)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Control Marantz via UPnP AVTransport")
    parser.add_argument("command", choices=["info", "play", "pause", "stop", "seturi"], help="Command to send")
    parser.add_argument("--uri", help="URI to stream (used with seturi)")
    args = parser.parse_args()

    if args.command == "info":
        get_transport_info()
    elif args.command == "play":
        play()
    elif args.command == "pause":
        pause()
    elif args.command == "stop":
        stop()
    elif args.command == "seturi":
        if not args.uri:
            print("❌ You must specify --uri with seturi")
        else:
            set_uri(args.uri)
