import pygame
import random
import time
from collections import deque
import ipaddress
import copy

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 1600, 800

LOG_ENTRY_HEIGHT = 12
SCROLL_SPEED = 20
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.font.init()
font = pygame.font.SysFont('Arial', 18)
small_font = pygame.font.SysFont('Arial', 16)
very_small_font = pygame.font.SysFont('Arial', 10)

# constants
SCROLL_BUTTON_SIZE = 12
SCROLL_BUTTON_COLOR = (200, 200, 200)

# Colors and other constants
COLORS = {
    'host': (0, 255, 0),
    'router': (255, 0, 0),
    'switch': (0, 0, 255),
    'hub': (128, 0, 128),
    'bridge': (255, 165, 0),
    'wire': (200, 200, 200),
    'text': (255, 255, 255),
    'background': (30, 30, 30),
    'panel': (50, 50, 50),
    'button': (100, 100, 100),
    'selected': (255, 255, 0),
    'input_bg': (80, 80, 80),
    'input_text': (200, 200, 200),
    'example_text': (150, 150, 150),
    'log_box_background':(50, 50, 50),
}

########################################################################
# Right Panel: Device Configuration Panel
########################################################################
class DeviceConfigPanel:
    def __init__(self):
        # Right panel occupies the rightmost 400 pixels.
        self.rect = pygame.Rect(WIDTH - 400, 0, 400, HEIGHT)
        self.fields = {}  # Dict of field_name -> dict(label, value, rect, example, active)
        self.active_field = None  # Name of the currently active field
        self.example_values = {
            'ip': '192.168.1.10',
            'subnet': '255.255.255.0',
            'gateway': '192.168.1.1',
            'interface': '10.0.0.1',  # For interface IPs
            'mask': '255.255.255.0',  # For interface masks
            'route': '10.0.0.0/24',
            'next': '192.168.1.2'
        }

        # Save button positioned near bottom-right of panel.
        self.save_button = pygame.Rect(WIDTH - 120, HEIGHT - 50, 100, 40)
        self.current_device = None
        self.interface_fields = []  # Field names for interfaces
        self.cursor_visible = True
        self.cursor_timer = 0

    def setup_fields(self, device):
        """Set up fields based on the device type."""
        self.current_device = device
        self.fields.clear()
        self.active_field = None
        self.interface_fields = []
        y = 20

        # Common fields for all devices
        self.add_field('ip', 'IP Address:', device.ip, y)
        y += 50
        self.add_field('subnet', 'Subnet Mask:', device.subnet_mask, y)
        y += 50

        if device.type == 'host':
            self.add_field('gateway', 'Default Gateway:', device.gateway, y)
            y += 50
        elif device.type == 'router':
            # For routers, show interface configuration for each port.
            for i in range(4):
                intf = device.interfaces.get(i, {'ip': '', 'mask': ''})
                self.add_field(f'interface_ip_{i}', f'Interface {i+1} IP:', intf.get('ip', ''), y)
                y += 40
                self.add_field(f'interface_mask_{i}', f'Interface {i+1} Mask:', intf.get('mask', ''), y)
                y += 40
                self.interface_fields.extend([f'interface_ip_{i}', f'interface_mask_{i}'])
            y += 20
            # Existing routing table entries, if any.
            for i, route in enumerate(device.routing_table):
                self.add_field(f'route_net_{i}', f'Route {i+1} Network:', route.get('network', ''), y)
                y += 40
                self.add_field(f'route_next_{i}', f'Route {i+1} Next Hop:', route.get('next_hop', ''), y)
                y += 40
            y += 20
            # Fields to add a new route.
            self.add_field('new_route_net', 'New Route Network:', '', y)
            y += 40
            self.add_field('new_route_next', 'New Route Next Hop:', '', y)
            y += 50

    def add_field(self, name, label, value, y):
        """Add a field with its label, current value, a rectangle for input, example text, and active flag."""
        key = name.split('_')[0]
        self.fields[name] = {
            'label': label,
            'value': value,
            'rect': pygame.Rect(WIDTH - 380, y, 340, 30),
            'example': self.example_values.get(key, ''),
            'active': False
        }

    def draw(self, surface):
        # Only draw if a device is selected.
        if not self.current_device:
            return

        # Draw panel background.
        pygame.draw.rect(surface, COLORS['panel'], self.rect)
        title = font.render(f"{self.current_device.type.upper()} Configuration", True, COLORS['text'])
        surface.blit(title, (WIDTH - 380, 10))

        # Update cursor blinking (toggle every 500 ms)
        self.cursor_timer += clock.get_time()
        if self.cursor_timer > 500:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

        # Draw each field.
        for name, field in self.fields.items():
            # Draw the field background.
            pygame.draw.rect(surface, COLORS['input_bg'], field['rect'], border_radius=3)
            # If field is active, show its value (or empty) and a blinking cursor.
            if field['active']:
                text = field['value']
                if self.cursor_visible:
                    text += "|"
                text_color = COLORS['input_text']
            else:
                # If no value has been entered, show the example (in grey).
                if field['value'] == "":
                    text = field['example']
                    text_color = COLORS['example_text']
                else:
                    text = field['value']
                    text_color = COLORS['input_text']
            label_surf = font.render(field['label'], True, COLORS['text'])
            text_surf = font.render(text, True, text_color)
            surface.blit(label_surf, (field['rect'].x, field['rect'].y - 20))
            surface.blit(text_surf, (field['rect'].x + 5, field['rect'].y + 5))
            # If active, draw a border.
            if field['active']:
                pygame.draw.rect(surface, COLORS['selected'], field['rect'], 2, border_radius=3)

        # Draw save button.
        pygame.draw.rect(surface, COLORS['button'], self.save_button, border_radius=5)
        save_text = font.render("SAVE", True, COLORS['text'])
        surface.blit(save_text, (self.save_button.x + 30, self.save_button.y + 10))

########################################################################
# Device Class
########################################################################
class Device:
    def __init__(self, x, y, device_type):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.type = device_type  # 'host', 'router', 'switch', etc.
        self.connections = []    # Devices connected by wires.
        self.ports = []          # For routers/switches.
        self.mac = ":".join(f"{random.randint(0,255):02x}" for _ in range(6))
        self.ip = ""
        self.subnet_mask = ""
        self.gateway = ""
        self.arp_table = {}
        self.mac_table = {}
        self.routing_table = []  # List of dicts, each with keys 'network' and 'next_hop'
        self.interfaces = {}     # For routers: {port: {'ip': '', 'mask': ''}}
        self.selected = False
        self.pending_packets = {}  # {destination_ip: [packets]} (like a router buffer)

        if self.type in ['router', 'switch']:
            self.ports = [None] * 4

    def get_available_port(self):
        for i, port in enumerate(self.ports):
            if port is None:
                return i
        return -1

    def connect_port(self, port_num, device):
        if 0 <= port_num < len(self.ports):
            self.ports[port_num] = device

    def draw(self, surface, sim):
        color = COLORS[self.type]
        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        # Draw highlight if active
        if self == sim.active_device and pygame.time.get_ticks() < sim.highlight_end_time:
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 4, border_radius=8)

        if self.selected:
            pygame.draw.rect(surface, COLORS['selected'], self.rect, 3, border_radius=8)
        if self.type in ['router', 'switch']:
            for i in range(4):
                port_color = (0, 255, 0) if self.ports[i] else (255, 0, 0)
                pygame.draw.circle(surface, port_color, (self.rect.right - 15, self.rect.top + 15 + i*15), 3)

        # random simple network:
        if self.type == 'host':
            # Draw IP text
            text = font.render(self.ip, True, COLORS['text'])
            surface.blit(text, (self.rect.centerx - 40, self.rect.bottom + 5))
        elif self.type == 'router':
            # Draw interface IPs
            for i, intf in self.interfaces.items():
                text = font.render(intf['ip'], True, COLORS['text'])
                surface.blit(text, (self.rect.right + 5, self.rect.top + 15 + i * 20))

########################################################################
# Left Panel: Simple Panel for Adding/Connecting/Deleting/Setting Task
########################################################################
class LeftPanel:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 400, HEIGHT)
        self.buttons = {
            'host': {'rect': pygame.Rect(10, 50, 180, 40), 'label': "Add Host (H)"},
            'router': {'rect': pygame.Rect(10, 100, 180, 40), 'label': "Add Router (R)"},
            'switch': {'rect': pygame.Rect(10, 150, 180, 40), 'label': "Add Switch (S)"},
            'connect': {'rect': pygame.Rect(10, 250, 180, 40), 'label': "Connect Devices (C)"},
            'delete': {'rect': pygame.Rect(10, 300, 180, 40), 'label': "Delete Device (D)"},
            'set_task': {'rect': pygame.Rect(10, 400, 180, 40), 'label': "Set Task (T)"},
            'run': {'rect': pygame.Rect(10, 450, 180, 40), 'label': "Run Simulation"},
            'create_random': {'rect': pygame.Rect(10, 500, 220, 40), 'label': "Create Random Network"},
            # 'prev_event': {'rect': pygame.Rect(10, 550, 180, 40),'label': "Previous Event"},
            # 'next_event':{'rect': pygame.Rect(10, 600, 180, 40),'label': "Next Event"}
        }
        self.current_action = None

    def draw(self, surface):
        pygame.draw.rect(surface, COLORS['panel'], self.rect)

        for btn in self.buttons.values():
            pygame.draw.rect(surface, COLORS['button'], btn['rect'], border_radius=5)
            text = font.render(btn['label'], True, COLORS['text'])
            surface.blit(text, (btn['rect'].x + 10, btn['rect'].y + 10))

########################################################################
# Network Simulator Class
########################################################################
class NetworkSimulator:
    def __init__(self):
        self.devices = []
        self.wires = []  # Each wire is a tuple: (device1, device2, port1, port2)
        self.selected_device = None
        self.left_panel = LeftPanel()
        self.panel = DeviceConfigPanel()  # Right configuration panel
        self.event_queue = deque()
        self.simulation_speed = 0.5  # Seconds between simulation steps
        self.task = None  # A tuple: (source_device, destination_device)
        self.simulation_running = False
        self.active_device = None
        self.highlight_end_time = 0  # Timestamp when highlight should end

        self.event_snapshots = []  # List to hold snapshots (deep copies) of the network state
        self.current_event_index = -1  # Pointer to the current event snapshot (-1 means none have run yet)
        self.simulation_event_logs = []  # Holds the logs for the most recently processed event

    def take_snapshot(self):
        """Take a deep copy snapshot of the current network state."""
        return {
            'devices': copy.deepcopy(self.devices),
            'wires': copy.deepcopy(self.wires),
            'event_queue': copy.deepcopy(self.event_queue)
        }

    def restore_snapshot(self, snapshot):
        """Restore the network state from a snapshot."""
        self.devices = copy.deepcopy(snapshot['devices'])
        self.wires = copy.deepcopy(snapshot['wires'])
        self.event_queue = copy.deepcopy(snapshot['event_queue'])

    def log_event(self, message):
        """Log a message for the current event and print it."""
        print(message, end="\n")
        self.simulation_event_logs.append(message)

    def handle_next_event(self):
        """Process one event from the queue after recording a snapshot."""
        if self.event_queue:
            self.simulation_event_logs = []  # Clear logs for the new event
            snapshot = self.take_snapshot()
            self.event_snapshots.append(snapshot)
            self.current_event_index += 1

            event = self.event_queue.popleft()
            self.process_next_event()
        else:
            self.log_event("No more events in the queue.")

    def handle_previous_event(self):
        """Revert the network state to the previous snapshot."""
        if self.current_event_index > 0:
            self.current_event_index -= 1
            snapshot = self.event_snapshots[self.current_event_index]
            self.restore_snapshot(snapshot)
            self.log_event("Reverted to previous event snapshot.")
        else:
            self.log_event("No previous event to revert to.")

    def set_active_device(self, device):
        self.active_device = device
        self.highlight_end_time = pygame.time.get_ticks() + 1000  # 1 second duration

    def add_device(self, device_type, pos):
        x, y = pos
        new_device = Device(x - 40, y - 40, device_type)
        self.devices.append(new_device)
        print(f"Added {device_type} at ({x}, {y})")

    def delete_device(self, device):
        for conn in device.connections[:]:
            self.disconnect_devices(device, conn)
        if device in self.devices:
            self.devices.remove(device)
        print(f"Removed {device.type}")

    def disconnect_devices(self, device1, device2):
        if device2 in device1.connections:
            device1.connections.remove(device2)
        if device1 in device2.connections:
            device2.connections.remove(device1)
        self.wires = [w for w in self.wires if not ((w[0] == device1 and w[1] == device2) or (w[0] == device2 and w[1] == device1))]

    def connect_devices(self, device1, device2):
        port1 = device1.get_available_port() if device1.type in ['router', 'switch'] else -1
        port2 = device2.get_available_port() if device2.type in ['router', 'switch'] else -1
        if port1 != -1:
            device1.connect_port(port1, device2)
        if port2 != -1:
            device2.connect_port(port2, device1)
        device1.connections.append(device2)
        device2.connections.append(device1)
        self.wires.append((device1, device2, port1, port2))
        print(f"Connected {device1.type} to {device2.type}")

    def set_task(self, source, destination):
        self.task = (source, destination)
        print(f"Task set: {source.ip} -> {destination.ip}")

    def start_simulation(self):
        if not self.task:
            print("No task set!")
            return
        src, dst = self.task
        print(f"=== Starting simulation from {src.ip} to {dst.ip} ===")
        self.event_queue.append(('send', src, dst, 'Hello', [src]))
        self.simulation_running = True

    def process_next_event(self):
        if not self.event_queue:
            return False

        self.log_event("↓↓↓↓↓EVENT↓↓↓↓↓")
        event = self.event_queue.popleft()
        event_type = event[0]
        if event_type == 'send':
            self.handle_send(*event[1:])
        elif event_type == 'forward':
            self.handle_forward(*event[1:])
        elif event_type == 'arp_request':
            self.handle_arp_request(*event[1:])
        elif event_type == 'arp_response':
            self.handle_arp_response(*event[1:])
        self.log_event("↑↑↑↑↑END OF EVENT↑↑↑↑↑\n")
        return True

    def ip_in_cidr(self,ip, cidr):
        """
        Return True if the given IP (a string) is within the CIDR network.
        For example, ip_in_cidr("10.0.0.5", "10.0.0.0/24") returns True.
        """
        try:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
        except ValueError:
            return False

    def get_source_ip(self, device, dst_ip):
        """
        For devices that have a routing table and multiple interfaces,
        return the IP address of the interface that is appropriate for reaching dst_ip.
        If no matching route is found, fall back to the first available interface,
        or, if none, simply return device.ip.
        """
        if hasattr(device, 'routing_table') and device.routing_table and device.interfaces:
            for route in device.routing_table:
                if self.ip_in_cidr(dst_ip, route['network']):
                    # route['interface'] is assumed to be the index of the interface.
                    if route['interface'] in device.interfaces:
                        return device.interfaces[route['interface']]['ip']
            # Fallback: return the IP of the first interface (if any)
            first_interface = list(device.interfaces.values())[0]
            return first_interface['ip']
        return device.ip


    def handle_send(self, src, dst, payload, path):
        self.set_active_device(src)

        # Only proceed if host has connections
        if not src.connections:
            self.log_event(f"[HOST {src.ip}] Cannot send - no network connection!")
            return

        self.log_event(f"\n[HOST {src.ip}] Initiating send to {dst.ip}")

        # Validate destination network
        if not self.ip_in_network(dst.ip, src.subnet_mask, src.ip):
            self.log_event(f"[HOST {src.ip}] Destination not local, using gateway {src.gateway}")
            if not src.gateway:
                self.log_event("[HOST] No gateway configured!")
                return
            dst_ip = src.gateway
        else:
            dst_ip = dst.ip

        # ARP resolution
        if dst_ip not in src.arp_table:
            self.log_event(f"[HOST {src.ip}] ARP lookup failed for {dst_ip}")

            self.log_event(f"[{src.ip}] Buffering packet while ARP resolves")
            if dst_ip not in src.pending_packets:
                src.pending_packets[dst_ip] = []
            src.pending_packets[dst_ip].append({
                'dst': dst,
                'payload': payload,
                'path': path
            })

            # Send ARP request through first connected interface
            arp_frame = {
                'src_mac': src.mac,
                'dst_mac': "ff:ff:ff:ff:ff:ff",
                'src_ip': self.get_source_ip(src, dst_ip),
                'dst_ip': dst_ip,
                'payload': 'ARP_REQUEST',
                'ttl': 64
            }
            next_hop = src.connections[0]
            new_path = path.copy()
            new_path.append(next_hop)
            self.event_queue.append(('forward', next_hop, arp_frame, new_path))
            return

        # Create frame and send through connected interface
        frame = {
            'src_mac': src.mac,
            'dst_mac': src.arp_table[dst_ip],
            'src_ip': src.ip,
            'dst_ip': dst.ip,
            'payload': payload,
            'ttl': 64
        }
        self.log_event(f"[HOST {src.ip}] Sending frame via {src.connections[0].type}")
        next_hop = src.connections[0]
        new_path = path.copy()
        new_path.append(next_hop)
        self.event_queue.append(('forward', next_hop, frame, new_path))


    def handle_forward(self, current_device, frame, path):
        self.set_active_device(current_device)

        frame['ttl'] -= 1
        if frame['ttl'] <= 0:
            self.log_event("Packet TTL expired!")
            return

        self.log_event(f"\n[{current_device.type.upper()}] {current_device.mac} processing frame:")
        self.log_event(f"From: {frame['src_mac']} ({frame['src_ip']})")
        self.log_event(f"To: {frame['dst_mac']} ({frame['dst_ip']})")

        if current_device.type == 'host':
            self.host_logic(current_device, frame, path)
        elif current_device.type == 'switch':
            self.switch_logic(current_device, frame, path)
        elif current_device.type == 'router':
            self.router_logic(current_device, frame, path)

    def host_logic(self, host, frame, path):
        # Only process frames addressed to this host's MAC or broadcast
        if frame['dst_mac'] not in [host.mac, "ff:ff:ff:ff:ff:ff"]:
            self.log_event(f"[HOST {host.ip}] Ignoring frame not addressed to us")
            return

        # Handle ARP responses first
        if frame['payload'] == 'ARP_RESPONSE':
            self.log_event(f"[HOST {host.ip}] Received ARP response for {frame['src_ip']}")
            host.arp_table[frame['src_ip']] = frame['src_mac']

            # Resend pending packets for this IP
            if frame['src_ip'] in host.pending_packets:
                for pkt in host.pending_packets[frame['src_ip']]:
                    self.event_queue.appendleft(('send', host, pkt['dst'], pkt['payload'], pkt['path']))
                del host.pending_packets[frame['src_ip']]
            return

        # Handle ARP requests
        if frame['payload'] == 'ARP_REQUEST':
            # Learn requester's IP/MAC even if not for us
            host.arp_table[frame['src_ip']] = frame['src_mac']

            if frame['dst_ip'] == host.ip:
                self.log_event(f"[HOST {host.ip}] Responding to ARP")
                self.handle_arp_response(
                    target=host,
                    requester_ip=frame['src_ip'],
                    requester_mac=frame['src_mac'],
                    path=path
                )
            else:
                self.log_event(f"[HOST {host.ip}] Ignoring ARP frame not addressed to us")
            return

        # Handle normal IP packets
        if frame['dst_ip'] == host.ip:
            self.log_event(f"[HOST {host.ip}] Received payload: {frame['payload']}")

            # Check if this is the final ACK for the original task
            if frame['payload'] == 'ACK' and self.task and host == self.task[0]:
                print("\n=== SIMULATION BEHAVED AS EXPECTED | SUCCESS ===")
                self.log_event(f"Original sender {host.ip} received ACK from {frame['src_ip']}")
                self.simulation_running = False
                self.event_queue.clear()
                return

            # Only send ACK if this isn't already an ACK
            if frame['payload'] != 'ACK' and host.connections:
                response_frame = {
                    'src_mac': host.mac,
                    'dst_mac': frame['src_mac'],
                    'src_ip': self.get_source_ip(host, frame['src_ip']),
                    'dst_ip': frame['src_ip'],
                    'payload': 'ACK',
                    'ttl': 64
                }
                next_hop = host.connections[0]
                new_path = [host]
                self.event_queue.append(('forward', next_hop, response_frame, new_path))
        else:
            self.log_event(f"[HOST {host.ip}] Ignoring packet not meant for us")

    def switch_logic(self, switch, frame, path):
        # Learn MAC address from incoming port
        incoming_device = path[-2] if len(path) > 1 else None
        if incoming_device:
            # Only learn if MAC isn't known or port changed
            if (frame['src_mac'] not in switch.mac_table or
                    switch.mac_table[frame['src_mac']] != incoming_device):
                switch.mac_table[frame['src_mac']] = incoming_device
                port = switch.ports.index(incoming_device)
                self.log_event(f"[SWITCH] Learned {frame['src_mac']} on port {port}")

        # Forwarding logic
        if frame['dst_mac'] in switch.mac_table:
            target = switch.mac_table[frame['dst_mac']]
            if target in switch.connections:
                self.log_event(f"[SWITCH] Forwarding to port {switch.ports.index(target)}")
                new_path = path.copy()
                new_path.append(target)
                self.event_queue.append(('forward', target, frame, new_path))
            else:
                self.log_event("[SWITCH] Known MAC but no connection, dropping")
        else:
            self.log_event("[SWITCH] Flooding to all connected ports")
            for conn in switch.connections:
                if conn != incoming_device and conn not in path:
                    new_path = path.copy()
                    new_path.append(conn)
                    self.event_queue.append(('forward', conn, frame, new_path))

    def router_logic(self, router, frame, path):
        # Handle ARP responses first
        if frame['payload'] == 'ARP_RESPONSE':
            self.log_event(f"[ROUTER] Received ARP response for {frame['src_ip']}")
            router.arp_table[frame['src_ip']] = frame['src_mac']

            # Resend pending packets for this IP
            if frame['src_ip'] in router.pending_packets:
                for pkt in router.pending_packets[frame['src_ip']]:
                    self.event_queue.appendleft(('forward', router, pkt['frame'], pkt['path']))
                del router.pending_packets[frame['src_ip']]
            return

        # First check for ARP requests
        if frame['payload'] == 'ARP_REQUEST' and frame['dst_mac'] == "ff:ff:ff:ff:ff:ff":
            # Learn requester's IP/MAC even if not for us
            router.arp_table[frame['src_ip']] = frame['src_mac']

            for intf in router.interfaces.values():
                if intf['ip'] == frame['dst_ip']:
                    self.log_event(f"[ROUTER] {intf['ip']} responding to ARP")
                    self.handle_arp_response(
                        target=router,
                        requester_ip=frame['src_ip'],
                        requester_mac=frame['src_mac'],
                        path=path
                    )
                    return
            return

        if frame['dst_mac'] != router.mac:
            self.log_event("[ROUTER] Frame not addressed to us, dropping")
            return

        self.log_event("[ROUTER] Processing IP packet")
        best_route = None
        for route in router.routing_table:
            if self.ip_in_cidr(frame['dst_ip'], route['network']):
                best_route = route
                break

        if not best_route:
            self.log_event("[ROUTER] No route found, dropping packet")
            return

        self.log_event(f"[ROUTER] Routing to interface {best_route['interface']}")
        # next_hop_ip = best_route['gateway'] or frame['dst_ip']
        next_hop_ip = frame['dst_ip']

        # Find actual connected interface
        interface_device = None
        for port, conn in enumerate(router.ports):
            if port == best_route['interface'] and conn is not None:
                interface_device = conn
                break

        if not interface_device:
            self.log_event("[ROUTER] Interface not connected, dropping")
            return

        # ARP resolution for next hop
        if next_hop_ip not in router.arp_table:
            self.log_event(f"[ROUTER] ARP lookup needed for {next_hop_ip}")
            self.log_event(f"[ROUTER] Buffering packet and sending ARP")
            if next_hop_ip not in router.pending_packets:
                router.pending_packets[next_hop_ip] = []
            router.pending_packets[next_hop_ip].append({
                'frame': frame,
                'path': path
            })
            self.event_queue.append(('arp_request', router, next_hop_ip, path))
            return

        # Create new frame for next hop
        new_frame = {
            'src_mac': router.mac,
            'dst_mac': router.arp_table[next_hop_ip],
            'src_ip': frame['src_ip'],
            'dst_ip': frame['dst_ip'],
            'payload': frame['payload'],
            'ttl': frame['ttl'] - 1
        }

        # Forward to connected interface
        new_path = path.copy()
        new_path.append(interface_device)
        self.event_queue.append(('forward', interface_device, new_frame, new_path))

    def handle_arp_request(self, requester, target_ip, path):
        self.set_active_device(requester)

        self.log_event(f"\n[ARP] Request from {requester.ip} for {target_ip}")

        # Common frame setup
        arp_frame = {
            'dst_mac': "ff:ff:ff:ff:ff:ff",
            'payload': 'ARP_REQUEST',
            'ttl': 64
        }

        if requester.type == 'router':
            # Router-specific ARP handling
            interface_num = None
            source_ip = None

            # Find which interface should handle this ARP request
            for route in requester.routing_table:
                if self.ip_in_cidr(target_ip, route['network']):
                    interface_num = route['interface']
                    source_ip = requester.interfaces.get(interface_num, {}).get('ip')
                    break

            if interface_num is None or not source_ip:
                self.log_event(f"[ARP] No route to {target_ip}, dropping request")
                return

            # Get connected device for this interface
            if interface_num >= len(requester.ports) or not requester.ports[interface_num]:
                self.log_event(f"[ARP] Interface {interface_num} not connected")
                return

            connected_device = requester.ports[interface_num]

            # Complete frame for router
            arp_frame.update({
                'src_mac': requester.mac,
                'src_ip': source_ip,
                'dst_ip': target_ip
            })

            # Send only through the target interface
            new_path = path.copy()
            new_path.append(connected_device)
            self.event_queue.append(('forward', connected_device, arp_frame, new_path))
        else:
            # Host/bridge/switch ARP handling
            arp_frame.update({
                'src_mac': requester.mac,
                'src_ip': requester.ip,
                'dst_ip': target_ip
            })

            # Broadcast to all connections
            self.log_event(f"[ARP] Broadcasting request through connected devices")
            for connected_device in requester.connections:
                new_path = path.copy()
                new_path.append(connected_device)
                self.event_queue.append(('forward', connected_device, arp_frame, new_path))


    def find_device_by_mac(self, mac):
        for device in self.devices:
            if device.mac == mac:
                return device
        return None

    def handle_arp_response(self, target, requester_ip, requester_mac, path):
        self.set_active_device(target)

        self.log_event(f"[ARP] {target.ip} responding to {requester_ip}")

        # Get the last hop from the path (device that delivered the request to us)
        if len(path) < 1:
            self.log_event("[ARP] Invalid path for response")
            return

        last_hop = path[-2]  # Last device that delivered the ARP request to us

        # Verify this last_hop is actually connected to us
        if last_hop not in target.connections:
            self.log_event(f"[ARP] {target.ip} has no connection to {last_hop.type}, dropping response")
            return

        # Create response frame
        response_frame = {
            'src_mac': target.mac,
            'dst_mac': requester_mac,  # Direct unicast to requester
            'src_ip': self.get_source_ip(target, requester_ip),
            'dst_ip': requester_ip,
            'payload': 'ARP_RESPONSE',
            'ttl': 64
        }

        # Always send back through the same interface that received the request
        self.log_event(f"[ARP] Sending response through {last_hop.type}")
        new_path = [target, last_hop]  # Start reverse path
        self.event_queue.append(('forward', last_hop, response_frame, new_path))

    def ip_in_network(self, ip, subnet_mask, source_ip):
        if not subnet_mask:
            return False
        ip_parts = list(map(int, ip.split('.')))
        src_parts = list(map(int, source_ip.split('.')))
        mask_parts = list(map(int, subnet_mask.split('.')))
        for i in range(4):
            if ip_parts[i] & mask_parts[i] != src_parts[i] & mask_parts[i]:
                return False
        return True

    def find_device_by_ip(self, ip):
        for device in self.devices:
            if device.ip == ip:
                return device
        return None

    def draw(self, surface):
        for device1, device2, _, _ in self.wires:
            pygame.draw.line(surface, COLORS['wire'], device1.rect.center, device2.rect.center, 2)
        for device in self.devices:
            device.draw(surface)
        pygame.draw.rect(surface, COLORS['panel'], self.left_panel.rect)
        self.left_panel.draw(surface)
        self.panel.draw(surface)

    def handle_config_save(self):
        if not self.panel.current_device:
            return
        device = self.panel.current_device
        device.ip = self.panel.fields['ip']['value']
        device.subnet_mask = self.panel.fields['subnet']['value']
        if device.type == 'host':
            device.gateway = self.panel.fields['gateway']['value']
        elif device.type == 'router':
            for i in range(4):
                ip_field = self.panel.fields.get(f'interface_ip_{i}', {})
                mask_field = self.panel.fields.get(f'interface_mask_{i}', {})
                ip_val = ip_field.get('value', '')
                mask_val = mask_field.get('value', '')
                if ip_val and mask_val:
                    device.interfaces[i] = {'ip': ip_val, 'mask': mask_val}
            new_routes = []
            for key in self.panel.fields:
                if key.startswith('route_net_'):
                    index = key.split('_')[-1]
                    net = self.panel.fields.get(f'route_net_{index}', {}).get('value', '')
                    next_hop = self.panel.fields.get(f'route_next_{index}', {}).get('value', '')
                    if net and next_hop:
                        new_routes.append({'network': net, 'next_hop': next_hop})
            new_net = self.panel.fields.get('new_route_net', {}).get('value', '')
            new_next = self.panel.fields.get('new_route_next', {}).get('value', '')
            if new_net and new_next:
                new_routes.append({'network': new_net, 'next_hop': new_next})
            device.routing_table = new_routes
        self.log_event(f"Saved configuration for {device.type} with IP {device.ip}")

    def create_random_network(self):
        # Clear existing network
        self.devices.clear()
        self.wires.clear()
        self.task = None

        # Create router with 2 interfaces
        router = Device(WIDTH // 2, HEIGHT // 2, 'router')
        router.interfaces = {
            0: {'ip': '192.168.1.1', 'mask': '255.255.255.0'},
            1: {'ip': '10.0.0.1', 'mask': '255.255.255.0'}
        }
        router.routing_table = [
            {'network': '192.168.1.0/24', 'interface': 0},
            {'network': '10.0.0.0/24', 'interface': 1}
        ]
        self.devices.append(router)

        # Create switches
        switch1 = Device(WIDTH // 2 - 200, HEIGHT // 2, 'switch')
        switch2 = Device(WIDTH // 2 + 200, HEIGHT // 2, 'switch')
        self.devices.extend([switch1, switch2])

        # Connect switches to router
        self.connect_devices(router, switch1)
        self.connect_devices(router, switch2)

        # Create hosts for network 192.168.1.0/24
        for i in range(2):
            host = Device(switch1.rect.x - 150, switch1.rect.y + i * 150, 'host')
            host.ip = f'192.168.1.{10 + i}'
            host.subnet_mask = '255.255.255.0'
            host.gateway = '192.168.1.1'
            self.connect_devices(switch1, host)
            self.devices.append(host)

        # Create host for network 10.0.0.0/24
        host = Device(switch2.rect.x + 150, switch2.rect.y, 'host')
        host.ip = '10.0.0.10'
        host.subnet_mask = '255.255.255.0'
        host.gateway = '10.0.0.1'
        self.connect_devices(switch2, host)
        self.devices.append(host)

        # Position devices
        for i, dev in enumerate(self.devices):
            if dev.type == 'switch':
                dev.rect.center = (router.rect.centerx + (-200 if i == 1 else 200), router.rect.centery)
            elif dev.type == 'host':
                dev.rect.center = (dev.rect.centerx, dev.rect.centery)

########################################################################
# Main Program
########################################################################
def main():
    sim = NetworkSimulator()
    running = True
    connecting = False
    first_device = None
    task_source = None
    log_box_rect = pygame.Rect(10, 580, 370, 200)

    up_button_rect = pygame.Rect(
        log_box_rect.right - SCROLL_BUTTON_SIZE + 10,
        log_box_rect.top + 25,
        SCROLL_BUTTON_SIZE,
        SCROLL_BUTTON_SIZE
    )

    down_button_rect = pygame.Rect(
        log_box_rect.right - SCROLL_BUTTON_SIZE +10,
        log_box_rect.bottom - SCROLL_BUTTON_SIZE - 5,
        SCROLL_BUTTON_SIZE,
        SCROLL_BUTTON_SIZE
    )
    log_scroll_offset = 0  # Initialize scroll position
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle mouse button down events.
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos

                mouse_pos = pygame.mouse.get_pos()

                if up_button_rect.collidepoint(mouse_pos):
                    log_scroll_offset = max(0, log_scroll_offset - LOG_ENTRY_HEIGHT)

                elif down_button_rect.collidepoint(mouse_pos):
                    log_content_height = len(sim.simulation_event_logs) * LOG_ENTRY_HEIGHT
                    max_scroll = max(0, log_content_height - (log_box_rect.height - 30))
                    log_scroll_offset = min(log_scroll_offset + LOG_ENTRY_HEIGHT, max_scroll)

                # Check if click is in left panel.
                if sim.left_panel.rect.collidepoint(x, y):
                    for btn_type, btn in sim.left_panel.buttons.items():
                        if btn['rect'].collidepoint(x, y):

                            if btn_type == 'run':
                                if sim.task:
                                    sim.start_simulation()
                            elif btn_type == 'create_random':
                                sim.create_random_network()
                            elif btn_type == 'prev_event':
                                sim.handle_previous_event()
                            elif btn_type == 'next_event':
                                sim.handle_next_event()
                            else:
                                sim.left_panel.current_action = btn_type
                            break
                    continue

                # Check if click is on right panel's save button.
                if sim.panel.save_button.collidepoint(x, y):
                    sim.handle_config_save()
                    continue

                # Check if click is inside any field in the right panel.
                field_clicked = False
                if sim.panel.current_device:
                    for name, field in sim.panel.fields.items():
                        if field['rect'].collidepoint(x, y):
                            # Set this field active and clear its value.
                            for other in sim.panel.fields.values():
                                other['active'] = False
                            field['active'] = True
                            sim.panel.active_field = name
                            # Clear the field's value if it equals the example (or if empty).
                            if field['value'] == "":
                                field['value'] = ""
                            field_clicked = True
                            break
                if field_clicked:
                    continue

                # Check if a device was clicked.
                clicked_device = None
                for device in reversed(sim.devices):
                    if device.rect.collidepoint(x, y):
                        clicked_device = device
                        break

                if clicked_device:
                    if sim.left_panel.current_action == 'delete':
                        sim.delete_device(clicked_device)
                        sim.left_panel.current_action = None
                    elif sim.left_panel.current_action == 'connect':
                        if not first_device:
                            first_device = clicked_device
                            first_device.selected = True
                        else:
                            sim.connect_devices(first_device, clicked_device)
                            first_device.selected = False
                            first_device = None
                            sim.left_panel.current_action = None
                    elif sim.left_panel.current_action == 'set_task':
                        if clicked_device.type == 'host':
                            if not task_source:
                                task_source = clicked_device
                                print(f"Task source set to {clicked_device.ip}")
                            else:
                                sim.set_task(task_source, clicked_device)
                                task_source = None
                                sim.left_panel.current_action = None
                    else:
                        sim.selected_device = clicked_device
                        clicked_device.selected = True
                        sim.panel.setup_fields(clicked_device)
                else:
                    if sim.left_panel.current_action in ['host', 'router', 'switch', 'hub', 'bridge']:
                        sim.add_device(sim.left_panel.current_action, (x, y))
                        sim.left_panel.current_action = None

            if event.type == pygame.MOUSEMOTION and sim.selected_device:
                dx, dy = event.rel
                sim.selected_device.rect.move_ip(dx, dy)

            if event.type == pygame.KEYDOWN and sim.panel.active_field:
                field = sim.panel.fields.get(sim.panel.active_field)
                if event.key == pygame.K_RETURN:
                    sim.panel.fields[sim.panel.active_field]['active'] = False
                    sim.panel.active_field = None
                elif event.key == pygame.K_BACKSPACE:
                    field['value'] = field['value'][:-1]
                else:
                    field['value'] += event.unicode

            if event.type == pygame.MOUSEBUTTONUP and sim.selected_device:
                sim.selected_device.selected = False
                sim.selected_device = None
            # handle mouse wheel events
            if event.type == pygame.MOUSEWHEEL:
                if log_box_rect.collidepoint(pygame.mouse.get_pos()):
                    # Calculate maximum valid scroll offset
                    log_content_height = len(sim.simulation_event_logs) * LOG_ENTRY_HEIGHT
                    max_scroll = max(0, log_content_height - log_box_rect.height + 30)

                    # Update scroll offset with clamping
                    log_scroll_offset = max(0, min(log_scroll_offset + event.y * SCROLL_SPEED, max_scroll))

        if sim.simulation_running:
            if sim.process_next_event():
                time.sleep(sim.simulation_speed)
            else:
                sim.simulation_running = False
                print("=== Simulation completed ===")

        screen.fill(COLORS['background'])
        for device1, device2, _, _ in sim.wires:
            pygame.draw.line(screen, COLORS['wire'], device1.rect.center, device2.rect.center, 2)
        for device in sim.devices:
            device.draw(screen,sim)
        pygame.draw.rect(screen, COLORS['panel'], sim.left_panel.rect)
        sim.left_panel.draw(screen)

        pygame.draw.rect(screen, COLORS['log_box_background'], log_box_rect)

        # Draw header
        header_text = small_font.render("Logs of the last event:", True, COLORS['text'])
        screen.blit(header_text, (log_box_rect.x + 5, log_box_rect.y + 5))

        # Calculate content parameters
        log_entries = len(sim.simulation_event_logs)
        log_content_height = log_entries * LOG_ENTRY_HEIGHT
        visible_height = log_box_rect.height - 30

        # Create scrollable content surface
        log_content_surface = pygame.Surface((log_box_rect.width - 20, max(log_content_height, visible_height)))
        log_content_surface.fill(COLORS['log_box_background'])

        # Render log entries
        if log_entries > 0:
            for i, log in enumerate(sim.simulation_event_logs):
                log_text = very_small_font.render(log, True, COLORS['text'])
                log_content_surface.blit(log_text, (5, i * LOG_ENTRY_HEIGHT))

        # Calculate and clamp scroll offset
        max_scroll = max(0, log_content_height - visible_height)
        log_scroll_offset = max(0, min(log_scroll_offset, max_scroll))

        # Draw visible portion
        screen.blit(log_content_surface,
                    (log_box_rect.x + 5, log_box_rect.y + 25),
                    (0, log_scroll_offset, log_box_rect.width - 20, visible_height))

        # Draw scroll bar only if needed
        if log_content_height > visible_height:
            scrollbar_height = (visible_height ** 2) / log_content_height
            scrollbar_pos = (log_scroll_offset / log_content_height) * (visible_height - scrollbar_height)

            pygame.draw.rect(screen, COLORS['text'],
                             (log_box_rect.right - 8,
                              log_box_rect.y + 25 + scrollbar_pos,
                              6,
                              scrollbar_height))

            pygame.draw.rect(screen, SCROLL_BUTTON_COLOR, up_button_rect)
            pygame.draw.polygon(screen, (0, 0, 0), [
                (up_button_rect.centerx, up_button_rect.top + 3),
                (up_button_rect.left + 3, up_button_rect.bottom - 3),
                (up_button_rect.right - 3, up_button_rect.bottom - 3)
            ])

            # Draw down button
            pygame.draw.rect(screen, SCROLL_BUTTON_COLOR, down_button_rect)
            pygame.draw.polygon(screen, (0, 0, 0), [
                (down_button_rect.centerx, down_button_rect.bottom - 3),
                (down_button_rect.left + 3, down_button_rect.top + 3),
                (down_button_rect.right - 3, down_button_rect.top + 3)
            ])

        sim.panel.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
