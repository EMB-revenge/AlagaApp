import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';

import '../../models/health_record.dart';
import '../../models/care_profile.dart';
import '../../config/theme.dart';
import '../../utils/constants.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/custom_app_bar.dart';
import '../../widgets/bottom_nav_bar.dart';
import '../../services/health_record_service.dart';
import '../../utils/error_handler.dart';

class HealthRecordsScreen extends StatefulWidget {
  final CareProfile careProfile;

  const HealthRecordsScreen({super.key, required this.careProfile});

  @override
  State<HealthRecordsScreen> createState() => _HealthRecordsScreenState();
}

class _HealthRecordsScreenState extends State<HealthRecordsScreen> {
  // Map to store the latest records for each health metric type
  final Map<HealthMetricType, HealthRecord?> _latestRecords = {};
  final HealthRecordService _healthRecordService = HealthRecordService();

  @override
  void initState() {
    super.initState();
    _fetchLatestHealthRecords();
  }

  Future<void> _fetchLatestHealthRecords() async {
    try {
      // Initialize the map with null values for each health metric type
      for (var type in HealthMetricType.values) {
        _latestRecords[type] = null;
      }

      // Fetch the latest record for each health metric type using the service
      final latestRecordsList =
          await _healthRecordService.getLatestHealthRecordsForCareProfile(
        widget.careProfile.id,
      );

      // Update the map with the fetched records
      for (var record in latestRecordsList) {
        _latestRecords[record.type] = record;
      }

      if (mounted) {
        setState(() {});
      }
    } catch (e) {
      if (mounted) {
        ErrorHandler.showSnackBar(
          context,
          '${AppConstants.errorFetchingHealthRecords}: $e',
        );
      }
    }
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
          Expanded(child: _buildHealthRecordsList()),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add),
        onPressed: () {
          _showAddHealthRecordDialog();
        },
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: 4, // Health tab
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
            'Health Records',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Keep track of Lemuel\'s well-being',
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

  Widget _buildHealthRecordsList() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildHealthMetricCard(
          HealthMetricType.heartRate,
          'Heart Rate',
          Icons.favorite,
          Colors.red.shade100,
          Colors.red,
        ),
        _buildHealthMetricCard(
          HealthMetricType.bloodPressure,
          'Blood Pressure',
          Icons.speed,
          Colors.blue.shade100,
          Colors.blue,
        ),
        _buildHealthMetricCard(
          HealthMetricType.glucoseLevel,
          'Glucose Levels',
          Icons.water_drop,
          Colors.amber.shade100,
          Colors.amber.shade800,
        ),
      ],
    );
  }

  Widget _buildHealthMetricCard(
    HealthMetricType type,
    String title,
    IconData icon,
    Color bgColor,
    Color iconColor,
  ) {
    final record = _latestRecords[type];
    final hasRecord = record != null;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
            ),
            child: Row(
              children: [
                Icon(icon, color: iconColor),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: iconColor,
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
                if (hasRecord) ...[
                  Text(
                    '${record.value} ${record.unit}',
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: AppTheme.textPrimaryColor,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Text(
                        'Last taken: ',
                        style: TextStyle(
                          fontSize: 14,
                          color: AppTheme.textSecondaryColor,
                        ),
                      ),
                      Text(
                        '${DateFormatter.formatTime(record.recordedAt)} · ${DateFormatter.formatDate(record.recordedAt)}',
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.textPrimaryColor,
                        ),
                      ),
                    ],
                  ),
                ] else
                  const Column(
                    children: [
                      Text(
                        'No records yet',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w500,
                          color: AppTheme.textSecondaryColor,
                        ),
                      ),
                    ],
                  ),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  onPressed: () =>
                      _showAddHealthRecordDialog(initialType: type),
                  icon: const Icon(Icons.add),
                  label: const Text('Add note'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: iconColor,
                    side: BorderSide(color: iconColor),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showAddHealthRecordDialog({HealthMetricType? initialType}) {
    final formKey = GlobalKey<FormState>();
    final valueController = TextEditingController();
    final notesController = TextEditingController();
    HealthMetricType selectedType = initialType ?? HealthMetricType.heartRate;
    String unit = HealthRecord.getDefaultUnit(selectedType);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Add ${HealthRecord.getDisplayName(selectedType)}'),
        content: Form(
          key: formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (initialType == null) ...[
                DropdownButtonFormField<HealthMetricType>(
                  value: selectedType,
                  decoration: const InputDecoration(
                    labelText: 'Health Metric',
                  ),
                  items: HealthMetricType.values.map((type) {
                    return DropdownMenuItem<HealthMetricType>(
                      value: type,
                      child: Text(HealthRecord.getDisplayName(type)),
                    );
                  }).toList(),
                  onChanged: (value) {
                    if (value != null) {
                      selectedType = value;
                      unit = HealthRecord.getDefaultUnit(value);
                    }
                  },
                ),
                const SizedBox(height: 16),
              ],
              TextFormField(
                controller: valueController,
                decoration: InputDecoration(
                  labelText: 'Value',
                  suffixText: unit,
                ),
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter a value';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: notesController,
                decoration: const InputDecoration(
                  labelText: 'Notes (optional)',
                ),
                maxLines: 2,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              if (formKey.currentState!.validate()) {
                try {
                  final user = FirebaseAuth.instance.currentUser;
                  if (user == null) {
                    throw Exception('User not authenticated');
                  }

                  final now = DateTime.now();
                  final newRecord = HealthRecord(
                    id: '', // Firestore will generate this ID
                    type: selectedType,
                    value: valueController.text.trim(),
                    unit: unit,
                    notes: notesController.text.trim(),
                    careProfileId: widget.careProfile.id,
                    userId: user.uid,
                    recordedAt: now,
                    createdAt: now,
                  );

                  // Add record using the service
                  await _healthRecordService.addHealthRecord(newRecord);

                  if (mounted) {
                    Navigator.of(this.context).pop();
                    _fetchLatestHealthRecords(); // Refresh the data
                    ScaffoldMessenger.of(this.context).showSnackBar(
                      const SnackBar(
                        content: Text('Health record added successfully'),
                      ),
                    );
                  }
                } catch (e) {
                  if (mounted) {
                    Navigator.of(this.context).pop();
                    ErrorHandler.showSnackBar(
                      this.context,
                      'Error adding health record: $e',
                    );
                  }
                }
              }
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }
}
