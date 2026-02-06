import 'dart:io';

import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

/// Accepts self-signed certificates for WSS connections to the desktop server
/// (e.g. wss://192.168.x.x:8765). Used when connecting to local/private IPs.
class SnapInterviewHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback = (X509Certificate cert, String host, int port) {
        // Only accept self-signed for private/LAN IPs
        final isPrivate = host.startsWith('10.') ||
            host.startsWith('192.168.') ||
            host.startsWith('172.') ||
            host == 'localhost' ||
            host == '127.0.0.1';
        return isPrivate;
      };
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  HttpOverrides.global = SnapInterviewHttpOverrides();
  runApp(const SnapInterviewApp());
}

class SnapInterviewApp extends StatelessWidget {
  const SnapInterviewApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'SnapInterview',
      theme: ThemeData.dark(),
      home: const HomeScreen(),
    );
  }
}