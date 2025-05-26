import 'package:flutter/material.dart';
import 'config/theme.dart';
import 'screens/medication/medication_list_screen.dart';
import 'models/care_profile.dart';

void main() {
  runApp(const AlagaApp());
}

class AlagaApp extends StatelessWidget {
  const AlagaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Alaga Care',
      theme: AppTheme.lightTheme,
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Demo care profile for testing
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
