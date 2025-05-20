import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
// Import the generated file (create this file using flutterfire_cli)
import 'firebase_options.dart';

void main() async {
  // Ensure Flutter is initialized
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  runApp(const MyApp());
}

// ... existing code for MyApp widget ...