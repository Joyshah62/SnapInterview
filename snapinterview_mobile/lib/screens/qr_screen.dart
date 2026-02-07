import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'setup_screen.dart';

class QRScreen extends StatefulWidget {
  const QRScreen({super.key});

  @override
  State<QRScreen> createState() => _QRScreenState();
}

class _QRScreenState extends State<QRScreen> {
  bool _navigated = false;

  // DEV: Update this IP to match your desktop's LAN IP shown in the Python terminal.
  void _testConnect() {
    const testWsUrl = "wss://192.168.1.105:8765/test";
    _connectAndListen(testWsUrl);
  }

  void _connectAndListen(String wsUrl) {
    if (_navigated) return;

    final channel = WebSocketChannel.connect(Uri.parse(wsUrl));
    debugPrint("Connecting to WebSocket: $wsUrl");

    channel.stream.listen(
      (event) {
        debugPrint("WebSocket received: $event");
        final data = jsonDecode(event);

        if (data["type"] == "server_message" && !_navigated) {
          _navigated = true;
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (_) => SetupScreen(channel: channel, wsUrl: wsUrl),
            ),
          );
        }
      },
      onError: (error) {
        debugPrint("WebSocket error: $error");
      },
      onDone: () {
        debugPrint("WebSocket closed");
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Scan QR Code")),
      body: Column(
        children: [
          Expanded(
            child: MobileScanner(
              onDetect: (BarcodeCapture capture) {
                if (_navigated) return;
                final barcode = capture.barcodes.first;
                final String? wsUrl = barcode.rawValue;
                if (wsUrl != null) {
                  _connectAndListen(wsUrl);
                }
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: ElevatedButton(
              onPressed: _testConnect,
              child: const Text("DEV: Connect without QR"),
            ),
          ),
        ],
      ),
    );
  }
}