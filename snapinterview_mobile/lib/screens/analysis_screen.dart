import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

/// Analysis screen shown after interview completes.
/// Shows loader + "We are evaluating, please wait" until evaluation_result is received, then displays result.
class AnalysisScreen extends StatefulWidget {
  final WebSocketChannel channel;
  final Stream stream;

  const AnalysisScreen({
    super.key,
    required this.channel,
    required this.stream,
  });

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen>
    with SingleTickerProviderStateMixin {
  bool _isLoading = true;
  Map<String, dynamic>? _evaluation;
  String? _error;
  StreamSubscription? _wsSubscription;
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _fadeAnimation = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeInOut),
    );
    _wsSubscription = widget.stream.listen((event) {
      if (event is String && mounted) {
        try {
          final data = jsonDecode(event) as Map<String, dynamic>?;
          if (data?['type'] == 'evaluation_result') {
            if (data!['success'] == true && data['result'] != null) {
              setState(() {
                _isLoading = false;
                _evaluation = data['result'] as Map<String, dynamic>;
                _error = null;
              });
            } else {
              setState(() {
                _isLoading = false;
                _evaluation = null;
                _error = data?['error'] as String? ?? 'Evaluation failed';
              });
            }
          }
        } catch (_) {}
      }
    });
  }

  @override
  void dispose() {
    _wsSubscription?.cancel();
    _fadeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('Interview Analysis'),
          automaticallyImplyLeading: true,
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircularProgressIndicator(),
              const SizedBox(height: 24),
              AnimatedBuilder(
                animation: _fadeAnimation,
                builder: (context, child) {
                  return Opacity(
                    opacity: _fadeAnimation.value,
                    child: Text(
                      'We are evaluating, please wait',
                      style: TextStyle(
                        fontSize: 16,
                        color: Theme.of(context)
                            .colorScheme
                            .onSurface
                            .withOpacity(0.7 + 0.3 * _fadeAnimation.value),
                      ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Interview Analysis')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline, size: 48, color: Colors.red.shade300),
                const SizedBox(height: 16),
                Text(
                  _error!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () => Navigator.of(context).popUntil((r) => r.isFirst),
                  child: const Text('Back to Home'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return _buildResultContent();
  }

  Widget _buildResultContent() {
    final e = _evaluation!;
    final overallScores = e['overall_scores'] as Map<String, dynamic>?;
    final overallScore = overallScores != null
        ? (overallScores['overall_score'] as num?)?.toDouble()
        : null;
    final hireSignal = e['hire_signal'] as String?;
    final strengths = _listStrings(e['strengths']);
    final weaknesses = _listStrings(e['weaknesses']);
    final finalFeedback = e['final_feedback_for_candidate'] as Map<String, dynamic>?;
    final summary = finalFeedback?['overall_summary'] as String?;
    final topImprovements = _listStrings(finalFeedback?['top_3_improvements']);
    final focusNext = finalFeedback?['what_to_focus_on_next'] as String?;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Interview Analysis'),
        automaticallyImplyLeading: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Center(
              child: Text(
                'Interview Complete',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            const SizedBox(height: 24),
            _buildScoreCard(overallScore, hireSignal),
            if (summary != null && summary.isNotEmpty) ...[
              const SizedBox(height: 20),
              const Text(
                'Summary',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                summary,
                style: const TextStyle(fontSize: 15, height: 1.4),
              ),
            ],
            if (strengths.isNotEmpty) ...[
              const SizedBox(height: 20),
              _buildSection('Strengths', strengths, Colors.green.shade700),
            ],
            if (weaknesses.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildSection('Areas to Improve', weaknesses, Colors.orange.shade700),
            ],
            if (topImprovements.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildSection('Top improvements', topImprovements, Colors.blue.shade700),
            ],
            if (focusNext != null && focusNext.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Text(
                'What to focus on next',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                focusNext,
                style: const TextStyle(fontSize: 15, height: 1.4),
              ),
            ],
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () =>
                    Navigator.of(context).popUntil((route) => route.isFirst),
                icon: const Icon(Icons.home),
                label: const Text('Back to Home'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<String> _listStrings(dynamic value) {
    if (value == null) return [];
    if (value is List) {
      return value
          .where((e) => e is String)
          .map((e) => e as String)
          .where((s) => s.isNotEmpty)
          .toList();
    }
    return [];
  }

  Widget _buildScoreCard(double? score, String? hireSignal) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('Overall Score ', style: TextStyle(fontSize: 16)),
                Text(
                  score != null
                      ? '${score.toStringAsFixed(1)} / ${score <= 5 ? 5 : 10}'
                      : '—',
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            if (hireSignal != null && hireSignal.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                hireSignal,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title, List<String> items, Color accent) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: accent,
          ),
        ),
        const SizedBox(height: 8),
        ...items.map(
          (item) => Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('• ', style: TextStyle(fontSize: 15, color: accent)),
                Expanded(
                  child: Text(
                    item,
                    style: const TextStyle(fontSize: 15, height: 1.3),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
