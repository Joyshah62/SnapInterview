import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class AudioService {
  static final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
  static final FlutterSoundPlayer _player = FlutterSoundPlayer();
  static StreamController<Uint8List>? _audioStream;
  static bool _isRunning = false;

  static Future<void> startStreaming(WebSocketChannel channel) async {
    // Request mic permission before trying to open the recorder
    final status = await Permission.microphone.request();
    if (!status.isGranted) {
      debugPrint("Microphone permission denied");
      return;
    }

    _audioStream = StreamController<Uint8List>();

    // Forward audio chunks to WebSocket
    _audioStream!.stream.listen((Uint8List data) {
      channel.sink.add(data);
    });

    await _recorder.openRecorder();
    await _recorder.startRecorder(
      codec: Codec.pcm16,
      sampleRate: 16000,
      numChannels: 1,
      toStream: _audioStream!.sink,
    );

    _isRunning = true;
    debugPrint("AudioService: streaming started");
  }

  static Future<void> stop() async {
    if (!_isRunning) return;
    _isRunning = false;

    await _recorder.stopRecorder();
    await _recorder.closeRecorder();
    await _audioStream?.close();
    _audioStream = null;

    debugPrint("AudioService: stopped");
  }

  /// Stop and close interviewer TTS playback (e.g. when ending interview).
  static Future<void> stopPlayback() async {
    try {
      await _player.stopPlayer();
    } catch (_) {}
    try {
      await _player.closePlayer();
    } catch (_) {}
    debugPrint("AudioService: playback stopped");
  }

  /// Play interviewer TTS MP3 sent from server (base64-encoded). Works for opening and LLM follow-up questions.
  /// [onPlaybackComplete] is called when this clip finishes (e.g. to navigate to analysis after closing message).
  static Future<void> playInterviewerAudio(
    String audioBase64, {
    void Function()? onPlaybackComplete,
  }) async {
    if (audioBase64.isEmpty) return;
    try {
      // Stop and close any current playback so we can play the new clip (opening or next question).
      try {
        await _player.stopPlayer();
      } catch (_) {}
      try {
        await _player.closePlayer();
      } catch (_) {}
      final bytes = base64Decode(audioBase64);
      final dir = Directory.systemTemp;
      final path = '${dir.path}/interviewer_${DateTime.now().millisecondsSinceEpoch}.mp3';
      final file = File(path);
      await file.writeAsBytes(bytes);
      await _player.openPlayer();
      await _player.startPlayer(
        fromURI: path,
        whenFinished: () async {
          try {
            await _player.closePlayer();
          } catch (_) {}
          try {
            await file.delete();
          } catch (_) {}
          onPlaybackComplete?.call();
        },
      );
      debugPrint("AudioService: playing interviewer audio");
    } catch (e) {
      debugPrint("AudioService: playInterviewerAudio error: $e");
      onPlaybackComplete?.call();
    }
  }
}