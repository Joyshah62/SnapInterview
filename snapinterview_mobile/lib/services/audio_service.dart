import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class AudioService {
  static final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
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
}