import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import 'constants.dart';

// Helper class to format dates and times consistently throughout the app
class DateFormatter {
  static final DateFormat _dateFormat = DateFormat(AppConstants.dateFormat);
  static final DateFormat _timeFormat = DateFormat(AppConstants.timeFormat);
  static final DateFormat _shortDateFormat = DateFormat(AppConstants.shortDateFormat);

  /// Formats a DateTime to a full date string (e.g., "January 15, 2024")
  static String formatDate(DateTime date) {
    return _dateFormat.format(date);
  }

  /// Formats a DateTime to a time string (e.g., "2:30 PM")
  static String formatTime(DateTime time) {
    return _timeFormat.format(time);
  }

  /// Formats a DateTime to a short date string (e.g., "Jan 15")
  static String formatShortDate(DateTime date) {
    return _shortDateFormat.format(date);
  }

  /// Formats a TimeOfDay to a time string
  static String formatTimeOfDay(TimeOfDay time) {
    final now = DateTime.now();
    final dateTime = DateTime(now.year, now.month, now.day, time.hour, time.minute);
    return formatTime(dateTime);
  }

  /// Checks if two dates are the same day
  static bool isSameDay(DateTime date1, DateTime date2) {
    return date1.year == date2.year &&
           date1.month == date2.month &&
           date1.day == date2.day;
  }

  /// Gets the start of day for a given date
  static DateTime getStartOfDay(DateTime date) {
    return DateTime(date.year, date.month, date.day);
  }

  /// Gets the end of day for a given date
  static DateTime getEndOfDay(DateTime date) {
    return DateTime(date.year, date.month, date.day, 23, 59, 59, 999);
  }
}