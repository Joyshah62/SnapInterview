import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'interview_screen.dart';

const List<String> roles = [
  'Software Engineer',
  'Product Manager',
  'Data Scientist',
  'UX Designer',
  'DevOps Engineer',
  'Marketing Manager',
  'Sales Representative',
  'Project Manager',
];

const List<String> difficulties = [
  'Easy',
  'Medium',
  'Hard',
];

class SetupScreen extends StatefulWidget {
  final WebSocketChannel channel;
  final Stream stream;
  final String wsUrl;
  const SetupScreen({super.key, required this.channel, required this.stream, required this.wsUrl});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  late WebSocketChannel _channel;
  late Stream _stream;
  String? _selectedRole;
  String? _selectedDifficulty;
  String? _resumeStatus;
  bool _resumeParsing = false;
  String? _pendingResumeName;
  final List<String> _pendingUploadTypes = [];
  StreamSubscription? _streamSubscription;

  @override
  void initState() {
    super.initState();
    _channel = widget.channel;
    _stream = widget.stream;
    _streamSubscription = _stream.listen(_onStreamMessage);
  }

  @override
  void dispose() {
    _streamSubscription?.cancel();
    super.dispose();
  }

  Future<void> _reconnect() async {
    final channel = WebSocketChannel.connect(Uri.parse(widget.wsUrl));
    final stream = channel.stream.asBroadcastStream();
    await stream.first;
    if (!mounted) return;
    _streamSubscription?.cancel();
    _streamSubscription = stream.listen(_onStreamMessage);
    setState(() {
      _channel = channel;
      _stream = stream;
    });
  }

  void _onStreamMessage(dynamic event) {
    if (event is! String) return;
    try {
      final data = jsonDecode(event);
      if (data["type"] == "document_upload_result" && _pendingUploadTypes.isNotEmpty) {
        final type = _pendingUploadTypes.removeAt(0);
        final success = data["success"] == true;
        if (mounted) {
          setState(() {
            if (type == "resume") {
              _resumeParsing = false;
              _resumeStatus = success ? (_pendingResumeName ?? "Uploaded") : "Failed";
            }
          });
        }
      }
    } catch (_) {}
  }

  Future<void> _pickAndUpload(String docType) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'docx'],
    );
    if (result == null || result.files.single.path == null) return;
    final path = result.files.single.path!;
    final name = result.files.single.name;
    final bytes = await File(path).readAsBytes();
    final base64Content = base64Encode(bytes);
    if (!mounted) return;
    await _reconnect();
    if (!mounted) return;
    if (mounted) {
      setState(() {
        _pendingUploadTypes.add(docType);
        _resumeParsing = true;
        _pendingResumeName = name;
      });
    }
    _channel.sink.add(jsonEncode({
      "type": "document_upload",
      "doc_type": docType,
      "filename": name,
      "content": base64Content,
    }));
  }

  void _sendAndContinue() {
    final payload = {
      "type": "interview_setup",
      "role": _selectedRole,
      "difficulty": _selectedDifficulty,
    };
    debugPrint("Sending setup: $payload");
    _channel.sink.add(jsonEncode(payload));
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => InterviewScreen(channel: _channel, stream: _stream),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final canContinue = _selectedRole != null && _selectedDifficulty != null;

    return Scaffold(
      appBar: AppBar(title: const Text("Interview Setup")),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 16),
            const Text(
              "Resume",
              style: TextStyle(fontSize: 16, color: Colors.white70),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: _resumeParsing ? null : () => _pickAndUpload("resume"),
                icon: const Icon(Icons.upload_file),
                label: Text(_resumeStatus ?? "Upload Resume"),
              ),
            ),
            if (_resumeParsing) ...[
              const SizedBox(height: 12),
              const _FadingParsingText(text: "Parsing resume…"),
            ],
            const SizedBox(height: 32),
            const Text(
              "Select Role",
              style: TextStyle(fontSize: 16, color: Colors.white70),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: DropdownButton<String>(
                isExpanded: true,
                value: _selectedRole,
                hint: const Text("Choose a role..."),
                onChanged: (value) {
                  setState(() => _selectedRole = value);
                },
                items: roles.map((role) {
                  return DropdownMenuItem<String>(
                    value: role,
                    child: Text(role),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 32),
            const Text(
              "Select Difficulty",
              style: TextStyle(fontSize: 16, color: Colors.white70),
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: DropdownButton<String>(
                isExpanded: true,
                value: _selectedDifficulty,
                hint: const Text("Choose difficulty..."),
                onChanged: (value) {
                  setState(() => _selectedDifficulty = value);
                },
                items: difficulties.map((d) {
                  return DropdownMenuItem<String>(
                    value: d,
                    child: Text(d),
                  );
                }).toList(),
              ),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: canContinue ? _sendAndContinue : null,
                child: const Text(
                  "Start Interview",
                  style: TextStyle(fontSize: 18),
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

/// Fading text shown while parsing (e.g. "Parsing resume…").
class _FadingParsingText extends StatefulWidget {
  final String text;

  const _FadingParsingText({required this.text});

  @override
  State<_FadingParsingText> createState() => _FadingParsingTextState();
}

class _FadingParsingTextState extends State<_FadingParsingText>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    )..repeat(reverse: true);
    _animation = Tween<double>(begin: 0.35, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Opacity(
          opacity: _animation.value,
          child: Text(
            widget.text,
            style: TextStyle(
              fontSize: 14,
              color: Theme.of(context).colorScheme.primary.withOpacity(0.9),
              fontStyle: FontStyle.italic,
            ),
          ),
        );
      },
    );
  }
}