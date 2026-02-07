import 'package:flutter/material.dart';

/// Analysis screen shown after interview completes (max questions reached).
/// Uses dummy data until real analysis is wired up.
class AnalysisScreen extends StatelessWidget {
  const AnalysisScreen({super.key});

  // Dummy data for display
  static const double _overallScore = 7.5;
  static const List<String> _strengths = [
    'Clear communication and structured answers',
    'Good technical knowledge in core areas',
    'Professional demeanor throughout',
  ];
  static const List<String> _areasToImprove = [
    'Provide more concrete examples from past experience',
    'Consider elaborating on problem-solving approach',
  ];
  static const String _summary =
      'Overall solid performance. The candidate demonstrated relevant knowledge '
      'and communicated clearly. With more specific examples, responses would be even stronger.';

  @override
  Widget build(BuildContext context) {
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
            const SizedBox(height: 8),
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
            _buildScoreCard(),
            const SizedBox(height: 20),
            _buildSection('Strengths', _strengths, Colors.green.shade700),
            const SizedBox(height: 16),
            _buildSection('Areas to Improve', _areasToImprove, Colors.orange.shade700),
            const SizedBox(height: 16),
            const Text(
              'Summary',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _summary,
              style: const TextStyle(fontSize: 15, height: 1.4),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => Navigator.of(context).popUntil((route) => route.isFirst),
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

  Widget _buildScoreCard() {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Overall Score ', style: TextStyle(fontSize: 16)),
            Text(
              '$_overallScore / 10',
              style: const TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
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
        ...items.map((item) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('• ', style: TextStyle(fontSize: 15, color: accent)),
                  Expanded(child: Text(item, style: const TextStyle(fontSize: 15, height: 1.3))),
                ],
              ),
            )),
      ],
    );
  }
}
