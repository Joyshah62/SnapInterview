import 'dart:convert';
import 'package:flutter/material.dart';
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
  const SetupScreen({super.key, required this.channel});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  String? _selectedRole;
  String? _selectedDifficulty;

  void _sendAndContinue() {
    final payload = {
      "type": "interview_setup",
      "role": _selectedRole,
      "difficulty": _selectedDifficulty,
    };

    debugPrint("Sending setup: $payload");
    widget.channel.sink.add(jsonEncode(payload));

    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => InterviewScreen(channel: widget.channel),
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