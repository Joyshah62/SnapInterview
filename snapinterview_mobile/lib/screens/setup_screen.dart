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
  final String wsUrl;
  const SetupScreen({super.key, required this.channel, required this.wsUrl});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  late WebSocketChannel _channel;
  String? _selectedRole;
  String? _selectedDifficulty;
  String? _resumeStatus;
  String? _jdStatus;

  @override
  void initState() {
    super.initState();
    _channel = widget.channel;
  }

  Future<WebSocketChannel> _reconnect() async {
    final channel = WebSocketChannel.connect(Uri.parse(widget.wsUrl));
    await channel.stream.first;
    return channel;
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
    final newChannel = await _reconnect();
    if (!mounted) return;
    setState(() => _channel = newChannel);
    _channel.sink.add(jsonEncode({
      "type": "document_upload",
      "doc_type": docType,
      "filename": name,
      "content": base64Content,
    }));
    if (mounted) {
      setState(() {
        if (docType == "resume") _resumeStatus = name;
        else _jdStatus = name;
      });
    }
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
        builder: (_) => InterviewScreen(channel: _channel),
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
              "Resume / Job Description",
              style: TextStyle(fontSize: 16, color: Colors.white70),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _pickAndUpload("resume"),
                    icon: const Icon(Icons.upload_file),
                    label: Text(_resumeStatus ?? "Upload Resume"),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _pickAndUpload("jd"),
                    icon: const Icon(Icons.upload_file),
                    label: Text(_jdStatus ?? "Upload JD"),
                  ),
                ),
              ],
            ),
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