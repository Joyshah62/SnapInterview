import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:permission_handler/permission_handler.dart';
import '../services/audio_service.dart';

class InterviewScreen extends StatefulWidget {
  final WebSocketChannel channel;
  const InterviewScreen({super.key, required this.channel});

  @override
  State<InterviewScreen> createState() => _InterviewScreenState();
}

class _InterviewScreenState extends State<InterviewScreen> {
  bool isRecording = false;
  // 🔹 Transcripts
  String liveSpeech = "";
  String finalTranscript = "";

  // 🔹 Camera
  CameraController? _cameraController;
  bool cameraReady = false;

  @override
  void initState() {
    super.initState();

    // Small delay to let QR scanner release camera
    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) _initCamera();
    });
  }

  void startRecording() {
    widget.channel.sink.add(jsonEncode({"type": "start_audio"}));

    AudioService.startStreaming(widget.channel);

    setState(() {
      isRecording = true;
      finalTranscript = "";
      liveSpeech = "";
    });
  }

  void stopRecording() {
    AudioService.stop();

    widget.channel.sink.add(jsonEncode({"type": "stop_audio"}));

    setState(() {
      isRecording = false;
    });
  }

  void endInterview() {
    // Stop recording if active
    if (isRecording) {
      AudioService.stop();
      widget.channel.sink.add(jsonEncode({"type": "stop_audio"}));
    }

    // 🔹 NEW: Send end_interview message to stop the server
    widget.channel.sink.add(jsonEncode({"type": "end_interview"}));

    // Give the message time to send before closing
    Future.delayed(const Duration(milliseconds: 200), () {
      // Close WebSocket connection
      widget.channel.sink.close();

      // Navigate back to QR scanner screen
      if (mounted) {
        Navigator.of(context).pop();
      }
    });
  }

  // ================= CAMERA =================
  Future<void> _initCamera() async {
    try {
      final status = await Permission.camera.request();
      if (!status.isGranted) return;

      final cameras = await availableCameras();
      if (cameras.isEmpty) return;

      final camera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _cameraController = CameraController(
        camera,
        ResolutionPreset.medium,
        enableAudio: false, // mic is handled by AudioService
      );

      await _cameraController!.initialize();

      if (!mounted) return;
      setState(() => cameraReady = true);
    } catch (e) {
      debugPrint("Camera init error: $e");
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  // ================= UI =================
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Interview in Progress"),
        automaticallyImplyLeading: false, // Remove back button
        actions: [
          // End Interview button in app bar
          TextButton.icon(
            icon: const Icon(Icons.exit_to_app, color: Colors.white),
            label: const Text(
              "End Interview",
              style: TextStyle(color: Colors.white),
            ),
            onPressed: () {
              // Show confirmation dialog
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text("End Interview"),
                  content: const Text(
                    "Are you sure you want to end this interview?",
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.of(ctx).pop(),
                      child: const Text("Cancel"),
                    ),
                    TextButton(
                      onPressed: () {
                        Navigator.of(ctx).pop(); // Close dialog
                        endInterview(); // End interview
                      },
                      style: TextButton.styleFrom(
                        foregroundColor: Colors.red,
                      ),
                      child: const Text("End"),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          const SizedBox(height: 12),

          // 📷 Small camera preview (square)
          Center(
            child: SizedBox(
              width: 300,
              height: 300,
              child: cameraReady
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: CameraPreview(_cameraController!),
                    )
                  : const Center(child: CircularProgressIndicator()),
            ),
          ),

          const SizedBox(height: 12),

          // 🎙 Controls
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  icon: const Icon(Icons.mic),
                  label: const Text("Start"),
                  onPressed: isRecording ? null : startRecording,
                ),
                const SizedBox(width: 16),
                ElevatedButton.icon(
                  icon: const Icon(Icons.stop),
                  label: const Text("Stop"),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                  onPressed: isRecording ? stopRecording : null,
                ),
              ],
            ),
          ),

          // 📝 Speech + Transcript
          Expanded(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              color: Colors.black,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 🎧 Listening indicator (only when recording)
                  if (isRecording) ...[
                    const Text(
                      "Listening...",
                      style: TextStyle(fontSize: 14, color: Colors.greenAccent),
                    ),
                    const SizedBox(height: 8),
                  ],

                  // Live speech text
                  Text(
                    liveSpeech.isEmpty ? "…" : liveSpeech,
                    style: const TextStyle(
                      fontSize: 16,
                      fontStyle: FontStyle.italic,
                    ),
                  ),

                  const Divider(height: 24),

                  // Final transcript
                  const Text(
                    "Transcript",
                    style: TextStyle(fontSize: 14, color: Colors.white70),
                  ),
                  const SizedBox(height: 6),

                  Expanded(
                    child: SingleChildScrollView(
                      child: Text(
                        finalTranscript.isEmpty
                            ? "Waiting for input..."
                            : finalTranscript,
                        style: const TextStyle(fontSize: 16),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}