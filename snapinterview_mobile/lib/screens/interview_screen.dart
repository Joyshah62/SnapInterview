import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:permission_handler/permission_handler.dart';
import '../services/audio_service.dart';
import 'analysis_screen.dart';

// Theme colors (library scope so all widgets in this file can use them)
const _kSurfaceBg = Color(0xFF1C1C1E);
const _kCardBg = Color(0xFF2C2C2E);
const _kAccent = Color(0xFF0A84FF);
const _kAccentRed = Color(0xFFFF453A);
const _kTextPrimary = Color(0xFFFFFFFF);
const _kTextSecondary = Color(0xFF8E8E93);

class InterviewScreen extends StatefulWidget {
  final WebSocketChannel channel;
  final Stream stream;
  const InterviewScreen({super.key, required this.channel, required this.stream});

  @override
  State<InterviewScreen> createState() => _InterviewScreenState();
}

class _InterviewScreenState extends State<InterviewScreen> {
  bool isRecording = false;
  String liveSpeech = "";
  String finalTranscript = "";
  String interviewerTranscript = "";
  bool _navigateToAnalysisWhenDone = false;
  StreamSubscription? _wsSubscription;

  CameraController? _cameraController;
  bool cameraReady = false;

  void _onPlaybackComplete() {
    if (!mounted) return;
    if (_navigateToAnalysisWhenDone) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => AnalysisScreen(
            channel: widget.channel,
            stream: widget.stream,
          ),
        ),
      );
    }
  }

  @override
  void initState() {
    super.initState();
    _wsSubscription = widget.stream.listen((event) {
      if (event is String) {
        try {
          final data = jsonDecode(event);
          if (!mounted) return;
          if (data["type"] == "interviewer_text" && data["text"] != null) {
            setState(() => interviewerTranscript = data["text"] as String);
          } else if (data["type"] == "interviewer_audio" && data["audio_base64"] != null) {
            AudioService.playInterviewerAudio(
              data["audio_base64"] as String,
              onPlaybackComplete: _onPlaybackComplete,
            );
          } else if (data["type"] == "interview_complete") {
            setState(() => _navigateToAnalysisWhenDone = true);
          } else if (data["type"] == "candidate_transcript" && data["text"] != null) {
            setState(() {
              finalTranscript = finalTranscript.isEmpty
                  ? (data["text"] as String)
                  : "$finalTranscript ${data["text"]}";
            });
          }
        } catch (_) {}
      }
    });
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
    setState(() => isRecording = false);
  }

  void endInterview() {
    if (isRecording) {
      AudioService.stop();
      widget.channel.sink.add(jsonEncode({"type": "stop_audio"}));
    }
    AudioService.stopPlayback();
    widget.channel.sink.add(jsonEncode({"type": "end_interview"}));
    Future.delayed(const Duration(milliseconds: 200), () {
      widget.channel.sink.close();
      if (mounted) Navigator.of(context).pop();
    });
  }

  // ================= CAMERA (correct aspect ratio = no stretch / convex look) =================
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
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
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
    _wsSubscription?.cancel();
    _cameraController?.dispose();
    super.dispose();
  }

  // ================= UI =================
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _kSurfaceBg,
      appBar: AppBar(
        title: const Text("Interview", style: TextStyle(fontWeight: FontWeight.w600)),
        backgroundColor: _kSurfaceBg,
        elevation: 0,
        automaticallyImplyLeading: false,
        actions: [
          TextButton.icon(
            icon: const Icon(Icons.close, color: _kTextSecondary, size: 20),
            label: const Text("End", style: TextStyle(color: _kTextSecondary, fontSize: 14)),
            onPressed: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  backgroundColor: _kCardBg,
                  title: const Text("End interview?", style: TextStyle(color: _kTextPrimary)),
                  content: const Text(
                    "Your progress will be saved. Are you sure?",
                    style: TextStyle(color: _kTextSecondary),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.of(ctx).pop(),
                      child: const Text("Cancel", style: TextStyle(color: _kTextSecondary)),
                    ),
                    TextButton(
                      onPressed: () {
                        Navigator.of(ctx).pop();
                        endInterview();
                      },
                      child: const Text("End", style: TextStyle(color: _kAccentRed)),
                    ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // ——— Camera preview (correct aspect ratio, no stretch) ———
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  color: _kCardBg,
                  constraints: const BoxConstraints(maxHeight: 220),
                  child: cameraReady && _cameraController != null
                      ? LayoutBuilder(
                          builder: (context, constraints) {
                            final ar = _cameraController!.value.aspectRatio;
                            // Use camera's native aspect ratio so the image is never stretched (fixes convex/wide face)
                            return Center(
                              child: AspectRatio(
                                aspectRatio: ar,
                                child: CameraPreview(_cameraController!),
                              ),
                            );
                          },
                        )
                      : const SizedBox(
                          height: 180,
                          child: Center(child: CircularProgressIndicator(color: _kAccent)),
                        ),
                ),
              ),
            ),

            // ——— Recording controls ———
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _ControlButton(
                    icon: Icons.mic,
                    label: "Start",
                    onPressed: isRecording ? null : startRecording,
                    color: _kAccent,
                  ),
                  const SizedBox(width: 20),
                  _ControlButton(
                    icon: Icons.stop_rounded,
                    label: "Stop",
                    onPressed: isRecording ? stopRecording : null,
                    color: _kAccentRed,
                  ),
                ],
              ),
            ),
            if (isRecording)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(color: Colors.greenAccent, shape: BoxShape.circle),
                    ),
                    const SizedBox(width: 8),
                    Text("Listening…", style: TextStyle(color: Colors.greenAccent.shade200, fontSize: 14)),
                  ],
                ),
              ),

            // ——— Transcripts ———
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const SizedBox(height: 4),
                    _SectionLabel(label: "Interviewer"),
                    const SizedBox(height: 6),
                    Expanded(
                      flex: 1,
                      child: _TranscriptCard(
                        text: interviewerTranscript.isEmpty ? "—" : interviewerTranscript,
                      ),
                    ),
                    const SizedBox(height: 12),
                    _SectionLabel(label: "Your transcript"),
                    const SizedBox(height: 6),
                    Expanded(
                      flex: 1,
                      child: _TranscriptCard(
                        text: finalTranscript.isEmpty ? "Waiting for your speech…" : finalTranscript,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String label;

  const _SectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: _kTextSecondary,
        letterSpacing: 0.2,
      ),
    );
  }
}

class _TranscriptCard extends StatelessWidget {
  final String text;

  const _TranscriptCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _kCardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF3A3A3C), width: 1),
      ),
      child: SingleChildScrollView(
        child: Text(
          text,
          style: const TextStyle(fontSize: 15, height: 1.4, color: _kTextPrimary),
        ),
      ),
    );
  }
}

class _ControlButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onPressed;
  final Color color;

  const _ControlButton({
    required this.icon,
    required this.label,
    required this.onPressed,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null;
    return Material(
      color: enabled ? color.withOpacity(0.2) : _kCardBg,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(icon, color: enabled ? color : _kTextSecondary, size: 22),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: enabled ? color : _kTextSecondary,
                  fontWeight: FontWeight.w600,
                  fontSize: 15,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
