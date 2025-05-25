import 'package:flutter/material.dart';

class ErrorHandler {
  static void showSnackBar(
    BuildContext context,
    String message,
    {
    Color backgroundColor = Colors.red,
  }) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: backgroundColor,
      ),
    );
  }
} 