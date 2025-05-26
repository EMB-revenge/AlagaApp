import 'package:flutter/material.dart';

import '../../models/medication.dart';
import '../../models/care_profile.dart';
import '../../config/theme.dart';
import '../../utils/constants.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/custom_app_bar.dart';
import '../../widgets/bottom_nav_bar.dart';
import '../../services/medication_service.dart';
import '../../utils/error_handler.dart';
import 'add_medication_screen.dart';

class MedicationListScreen extends StatefulWidget {
  final CareProfile careProfile;

  const MedicationListScreen({super.key, required this.careProfile});

  @override
  State<MedicationListScreen> createState() => _MedicationListScreenState();
}

class _MedicationListScreenState extends State<MedicationListScreen> {
  final MedicationService _medicationService = MedicationService();

  @override
  void initState() {
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: widget.careProfile.name,
      ),
      body: Column(
        children: [
          _buildHeader(),
          _buildDateCard(),
          Expanded(child: _buildMedicationsList()),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add),
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) =>
                  AddMedicationScreen(careProfile: widget.careProfile),
            ),
          ).then((_) {
            // Refresh the list when returning from add screen
            setState(() {});
          });
        },
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: 1, // Medications tab
        onTap: (index) {
          // Handle navigation
        },
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 16),
      color: AppTheme.primaryColor,
      child: const Column(
        children: [
          Text(
            AppConstants.pillReminderTitle,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          SizedBox(height: 8),
          Text(
            AppConstants.medicationReminderMessage,
            style: TextStyle(fontSize: 14, color: Colors.white),
          ),
        ],
      ),
    );
  }

  Widget _buildDateCard() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.pink.shade100,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.calendar_today, size: 16, color: Colors.pink),
          const SizedBox(width: 8),
          Text(
            'Today\'s date: ${DateFormatter.formatDate(DateTime.now())}',
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Colors.pink,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMedicationsList() {
    return StreamBuilder<List<Medication>>(
      stream: _medicationService
          .getMedicationsForCareProfile(widget.careProfile.id),
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(child: Text('Error: ${snapshot.error}'));
        }

        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        final medications = snapshot.data;

        if (medications == null || medications.isEmpty) {
          return const Center(child: Text('No medications found'));
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: medications.length,
          itemBuilder: (context, index) {
            final medication = medications[index];
            return _buildMedicationCard(medication);
          },
        );
      },
    );
  }

  Widget _buildMedicationCard(Medication medication) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.primaryColor.withAlpha(204),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
            ),
            child: Row(
              children: [
                const Icon(Icons.access_time, color: Colors.white),
                const SizedBox(width: 8),
                Text(
                  medication.time,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  medication.name,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.textPrimaryColor,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '${medication.dosage} - ${medication.frequency}',
                  style: const TextStyle(
                    fontSize: 14,
                    color: AppTheme.textSecondaryColor,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildActionButton(
                      'Skipped',
                      Colors.red.shade100,
                      Colors.red,
                      () => _updateMedicationStatus(
                        medication,
                        MedicationStatus.skipped,
                      ),
                    ),
                    const SizedBox(width: 16),
                    _buildActionButton(
                      'Taken',
                      Colors.green.shade100,
                      Colors.green,
                      () => _updateMedicationStatus(
                        medication,
                        MedicationStatus.taken,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButton(
    String text,
    Color bgColor,
    Color textColor,
    VoidCallback onPressed,
  ) {
    return Expanded(
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: bgColor,
          foregroundColor: textColor,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          padding: const EdgeInsets.symmetric(vertical: 12),
        ),
        child: Text(text),
      ),
    );
  }

  Future<void> _updateMedicationStatus(
    Medication medication,
    MedicationStatus status,
  ) async {
    try {
      await _medicationService.updateMedicationStatus(medication.id, status);

      // Show success message
      if (mounted) {
        ErrorHandler.showSnackBar(
          context,
          'Medication marked as ${status.toString().split('.').last}',
          backgroundColor:
              status == MedicationStatus.taken ? Colors.green : Colors.red,
        );
      }
    } catch (e) {
      // Show error message
      if (mounted) {
        ErrorHandler.showSnackBar(
          context,
          'Error updating medication: $e',
          backgroundColor: Colors.red,
        );
      }
    }
  }
}
