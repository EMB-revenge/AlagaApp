// All text strings and constants used throughout the app
class AppConstants {
  // App Information
  static const String appName = 'Alaga Care';
  static const String appVersion = '1.0.0';

  // Screen Titles
  static const String pillReminderTitle = 'Pill Reminder';
  static const String healthRecordsTitle = 'Health Records';
  static const String calendarTitle = 'Calendar';
  static const String addMedicationTitle = 'Add Medication';

  // Messages
  static const String medicationReminderMessage = 'Ensure Lemuel takes their meds on time!';
  static const String healthRecordsMessage = 'Track and monitor health metrics';
  static const String noMedicationsMessage = 'No medications scheduled for today';
  static const String noHealthRecordsMessage = 'No health records found';
  static const String noEventsMessage = 'No events for this day';

  // Error Messages
  static const String errorFetchingMedications = 'Error fetching medications';
  static const String errorFetchingHealthRecords = 'Error fetching health records';
  static const String errorFetchingEvents = 'Error fetching events';
  static const String errorAddingMedication = 'Error adding medication';
  static const String errorUpdatingMedication = 'Error updating medication';

  // Success Messages
  static const String medicationAddedSuccess = 'Medication added successfully';
  static const String medicationUpdatedSuccess = 'Medication updated successfully';
  static const String healthRecordAddedSuccess = 'Health record added successfully';

  // Form Labels
  static const String medicationNameLabel = 'Medication Name';
  static const String dosageLabel = 'Dosage';
  static const String frequencyLabel = 'Frequency';
  static const String timeLabel = 'Time';
  static const String notesLabel = 'Notes';

  // Button Labels
  static const String addButton = 'Add';
  static const String saveButton = 'Save';
  static const String cancelButton = 'Cancel';
  static const String deleteButton = 'Delete';
  static const String editButton = 'Edit';

  // Navigation Labels
  static const String homeTab = 'Home';
  static const String medicationsTab = 'Medications';
  static const String profileTab = 'Profile';
  static const String healthTab = 'Health';
  static const String calendarTab = 'Calendar';

  // Medication Frequencies
  static const List<String> medicationFrequencies = [
    'After breakfast, every morning before sleep',
    'Twice a day',
    'Once daily',
    'Every 8 hours',
    'Every 12 hours',
    'As needed',
  ];

  // Date Formats
  static const String dateFormat = 'MMMM d, yyyy';
  static const String timeFormat = 'h:mm a';
  static const String shortDateFormat = 'MMM d';
}