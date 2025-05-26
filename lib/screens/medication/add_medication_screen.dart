import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';

import '../../models/care_profile.dart';
import '../../config/theme.dart';
import '../../services/medication_service.dart';
import '../../models/medication.dart';
import '../../utils/error_handler.dart';
import '../../utils/constants.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/custom_app_bar.dart';

class AddMedicationScreen extends StatefulWidget {
  final CareProfile careProfile;

  const AddMedicationScreen({super.key, required this.careProfile});

  @override
  State<AddMedicationScreen> createState() => _AddMedicationScreenState();
}

class _AddMedicationScreenState extends State<AddMedicationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _dosageController = TextEditingController();
  final _timeController = TextEditingController();
  String _frequency = 'After breakfast, every morning before sleep';
  TimeOfDay _selectedTime = TimeOfDay.now();
  bool _isLoading = false;

  final List<String> _frequencyOptions = [
    'After breakfast, every morning before sleep',
    'Twice a day',
    'Once daily',
    'Every 8 hours',
    'Every 12 hours',
    'As needed',
  ];

  final MedicationService _medicationService = MedicationService();

  @override
  void dispose() {
    _nameController.dispose();
    _dosageController.dispose();
    _timeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const CustomAppBar(
        title: 'Add Medication',
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildMedicationIcon(),
                const SizedBox(height: 24),
                _buildMedicationNameField(),
                const SizedBox(height: 24),
                _buildFrequencyField(),
                const SizedBox(height: 24),
                _buildTimeField(),
                const SizedBox(height: 32),
                _buildAddButton(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMedicationIcon() {
    return Center(
      child: Container(
        width: 80,
        height: 80,
        decoration: BoxDecoration(
          color: AppTheme.primaryColor.withAlpha(51),
          borderRadius: BorderRadius.circular(40),
        ),
        child: const Icon(
          Icons.medication,
          size: 40,
          color: AppTheme.primaryColor,
        ),
      ),
    );
  }

  Widget _buildMedicationNameField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          AppConstants.medicationNameLabel,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.red.shade400,
          ),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: _nameController,
          decoration: InputDecoration(
            hintText: 'Enter medicine name here',
            prefixIcon: const Icon(Icons.medication_outlined),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
            filled: true,
            fillColor: Colors.grey.shade100,
          ),
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Please enter the medicine name';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildFrequencyField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          AppConstants.frequencyLabel,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.red.shade400,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(
            color: Colors.grey.shade100,
            borderRadius: BorderRadius.circular(8),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              isExpanded: true,
              value: _frequency,
              icon: const Icon(Icons.arrow_drop_down),
              items: _frequencyOptions.map((String option) {
                return DropdownMenuItem<String>(
                  value: option,
                  child: Text(option),
                );
              }).toList(),
              onChanged: (String? newValue) {
                if (newValue != null) {
                  setState(() {
                    _frequency = newValue;
                  });
                }
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTimeField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          AppConstants.timeLabel,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w500,
            color: Colors.red.shade400,
          ),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: _timeController,
          readOnly: true,
          decoration: InputDecoration(
            hintText: 'Enter time here',
            prefixIcon: const Icon(Icons.access_time),
            suffixIcon: const Icon(Icons.refresh),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
              borderSide: BorderSide.none,
            ),
            filled: true,
            fillColor: Colors.grey.shade100,
          ),
          onTap: () async {
            final TimeOfDay? pickedTime = await showTimePicker(
              context: context,
              initialTime: _selectedTime,
            );

            if (pickedTime != null) {
              setState(() {
                _selectedTime = pickedTime;
                _timeController.text = DateFormatter.formatTimeOfDay(pickedTime);
              });
            }
          },
          validator: (value) {
            if (value == null || value.isEmpty) {
              return 'Please select a time';
            }
            return null;
          },
        ),
      ],
    );
  }

  Widget _buildAddButton() {
    return SizedBox(
      width: double.infinity,
      height: 50,
      child: ElevatedButton(
        onPressed: _isLoading ? null : _saveMedication,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.primaryColor,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
        child: _isLoading
            ? const CircularProgressIndicator(color: Colors.white)
            : const Text(
                AppConstants.saveButton,
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
      ),
    );
  }



  Future<void> _saveMedication() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      try {
        final user = FirebaseAuth.instance.currentUser;
        if (user == null) {
          throw Exception('User not authenticated');
        }

        // Prepare medication data using the Medication model
        final now = DateTime.now();
        final newMedication = Medication(
          id: '', // Firestore will generate this ID
          name: _nameController.text.trim(),
          dosage: _dosageController.text.trim().isNotEmpty
              ? _dosageController.text.trim()
              : '1 tablet',
          frequency: _frequency,
          time: _timeController.text,
          careProfileId: widget.careProfile.id,
          userId: user.uid,
          status: MedicationStatus.pending,
          createdAt: now,
          updatedAt: now,
        );

        // Save to Firestore using the service
        await _medicationService.addMedication(newMedication);

        // Show success message and navigate back
        if (mounted) {
          ErrorHandler.showSnackBar(
            context,
            AppConstants.medicationAddedSuccess,
            backgroundColor: Colors.green,
          );
          Navigator.of(context).pop();
        }
      } catch (e) {
        // Show error message
        if (mounted) {
          ErrorHandler.showSnackBar(
            context,
            'Error adding medication: $e',
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }
}
