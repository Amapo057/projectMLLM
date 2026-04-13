import 'package:flutter/material.dart';

class OrbPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final center = Offset(cx, cy);
    final maxR = size.shortestSide / 2;

    // ── 1. 외곽 글로우 (어두운 파랑 방사형 그라디언트) ─────────
    canvas.drawCircle(
      center,
      maxR,
      Paint()
        ..shader = RadialGradient(
          colors: [
            const Color(0xFF0A4A96),
            const Color(0xFF06214A),
            Colors.black,
          ],
          stops: const [0.0, 0.6, 1.0],
        ).createShader(Rect.fromCircle(center: center, radius: maxR)),
    );

    // ── 2. 중간 링 (밝은 파랑) ──────────────────────────────────
    canvas.drawCircle(
      center,
      maxR * 0.72,
      Paint()
        ..shader = RadialGradient(
          colors: [
            const Color(0xFF4A90D9),
            const Color(0xFF1A5AAA),
            const Color(0xFF062870),
          ],
          stops: const [0.0, 0.5, 1.0],
        ).createShader(
            Rect.fromCircle(center: center, radius: maxR * 0.72)),
    );

    // ── 3. 내부 원 (흰빛 글로우) ────────────────────────────────
    canvas.drawCircle(
      center,
      maxR * 0.42,
      Paint()
        ..shader = RadialGradient(
          colors: [
            Colors.white,
            const Color(0xFFB8D8FF),
            const Color(0xFF3A78CC),
          ],
          stops: const [0.0, 0.4, 1.0],
        ).createShader(
            Rect.fromCircle(center: center, radius: maxR * 0.42)),
    );

    // ── 4. 중심 밝은 점 ──────────────────────────────────────────
    canvas.drawCircle(
      center,
      maxR * 0.13,
      Paint()
        ..shader = RadialGradient(
          colors: [Colors.white, const Color(0xFFCCE8FF)],
          stops: const [0.3, 1.0],
        ).createShader(
            Rect.fromCircle(center: center, radius: maxR * 0.13)),
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}