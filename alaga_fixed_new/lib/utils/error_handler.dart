import 'package:flutter/material.dart';

// Helper class to show error messages to users
class ErrorHandler {
  // Show a message at the bottom of the screen
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