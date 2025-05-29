// Main entry point for the Alaga Care app - a medication reminder and health tracking app
import 'package:flutter/material.dart';
import 'config/theme.dart';
import 'screens/medication/medication_list_screen.dart';
import 'models/care_profile.dart';

// App starts here
void main() {
  runApp(const AlagaApp());
}

// Root widget that sets up the app configuration
class AlagaApp extends StatelessWidget {
  const AlagaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Alaga Care',
      theme: AppTheme.lightTheme, // Custom theme from config
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false, // Hide debug banner
    );
  }
}

// Main home screen - entry point for users
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Create a demo profile for testing the app
    final demoProfile = CareProfile(
      id: 'demo_id',
      name: 'Lemuel',
      userId: 'demo_user',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text('Alaga Care'),
        centerTitle: true,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text(
              'Welcome to Alaga Care',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            // Button to navigate to medication list
            ElevatedButton(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => MedicationListScreen(
                      careProfile: demoProfile,
                    ),
                  ),
                );
              },
              child: const Text('View Medications'),
            ),
          ],
        ),
      ),
    );
  }
}
