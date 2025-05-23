import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:table_calendar/table_calendar.dart';

import '../../models/calendar_event.dart';
import '../../models/care_profile.dart';
import '../../config/theme.dart';
import '../../widgets/bottom_nav_bar.dart';
import '../../services/calendar_service.dart';

class CalendarScreen extends StatefulWidget {
  final CareProfile careProfile;

  const CalendarScreen({super.key, required this.careProfile});

  @override
  State<CalendarScreen> createState() => _CalendarScreenState();
}

class _CalendarScreenState extends State<CalendarScreen> {
  late DateTime _focusedDay;
  late DateTime _selectedDay;
  final DateFormat _dateFormat = DateFormat('MMMM d, yyyy');
  CalendarFormat _calendarFormat = CalendarFormat.month;
  Map<DateTime, List<CalendarEvent>> _events = {};
  List<CalendarEvent> _selectedEvents = [];

  final CalendarService _calendarService = CalendarService();

  @override
  void initState() {
    super.initState();
    _focusedDay = DateTime.now();
    _selectedDay = DateTime.now();
    _fetchEvents();
  }

  Future<void> _fetchEvents() async {
    try {
      // Clear existing events
      _events = {};

      // Fetch events from Firestore using the service
      final List<CalendarEvent> eventsList =
          await _calendarService.getEventsForMonth(
        widget.careProfile.id,
        _focusedDay, // Pass the month being displayed
      );

      // Process events and populate the map
      for (var event in eventsList) {
        final eventDate = DateTime(
          event.date.year,
          event.date.month,
          event.date.day,
        );

        if (_events[eventDate] == null) {
          _events[eventDate] = [];
        }
        _events[eventDate]!.add(event);
      }

      // Update selected events
      _updateSelectedEvents();

      if (mounted) {
        setState(() {});
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error fetching events: $e')));
      }
    }
  }

  void _updateSelectedEvents() {
    final selectedDate = DateTime(
      _selectedDay.year,
      _selectedDay.month,
      _selectedDay.day,
    );
    _selectedEvents = _events[selectedDate] ?? [];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Text(
          widget.careProfile.name.toUpperCase(),
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),
      body: Column(
        children: [
          _buildHeader(),
          _buildDateCard(),
          _buildCalendar(),
          const Divider(height: 1),
          Expanded(child: _buildEventsList()),
        ],
      ),
      bottomNavigationBar: BottomNavBar(
        currentIndex: 3, // Calendar tab
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
            'Calendar',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Never miss a moment of Alaga',
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
            'Today\'s date: ${_dateFormat.format(DateTime.now())}',
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

  Widget _buildCalendar() {
    return TableCalendar<CalendarEvent>(
      firstDay: DateTime.utc(2020, 1, 1),
      lastDay: DateTime.utc(2030, 12, 31),
      focusedDay: _focusedDay,
      calendarFormat: _calendarFormat,
      eventLoader: (day) {
        final normalizedDay = DateTime(day.year, day.month, day.day);
        return _events[normalizedDay] ?? [];
      },
      selectedDayPredicate: (day) {
        return isSameDay(_selectedDay, day);
      },
      onDaySelected: (selectedDay, focusedDay) {
        setState(() {
          _selectedDay = selectedDay;
          _focusedDay = focusedDay;
          _updateSelectedEvents();
        });
      },
      onFormatChanged: (format) {
        setState(() {
          _calendarFormat = format;
        });
      },
      onPageChanged: (focusedDay) {
        _focusedDay = focusedDay;
        _fetchEvents();
      },
      calendarStyle: CalendarStyle(
        markersMaxCount: 3,
        markerDecoration: const BoxDecoration(
          color: AppTheme.primaryColor,
          shape: BoxShape.circle,
        ),
        todayDecoration: BoxDecoration(
          color: AppTheme.primaryColor.withAlpha(128),
          shape: BoxShape.circle,
        ),
        selectedDecoration: const BoxDecoration(
          color: AppTheme.primaryColor,
          shape: BoxShape.circle,
        ),
      ),
      headerStyle: const HeaderStyle(
        formatButtonVisible: false,
        titleCentered: true,
        leftChevronIcon: Icon(Icons.chevron_left, color: AppTheme.primaryColor),
        rightChevronIcon: Icon(
          Icons.chevron_right,
          color: AppTheme.primaryColor,
        ),
        titleTextStyle: TextStyle(
          color: AppTheme.primaryColor,
          fontSize: 18,
          fontWeight: FontWeight.bold,
        ),
      ),
      calendarBuilders: CalendarBuilders(
        markerBuilder: (context, date, events) {
          if (events.isEmpty) return null;

          // Create a row of colored dots for each event type
          return Positioned(
            bottom: 1,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: events.take(3).map((event) {
                final CalendarEvent calEvent = event;
                return Container(
                  margin: const EdgeInsets.symmetric(horizontal: 1),
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: calEvent.getEventColor().withAlpha(51),
                  ),
                );
              }).toList(),
            ),
          );
        },
      ),
    );
  }

  Widget _buildEventsList() {
    if (_selectedEvents.isEmpty) {
      return const Center(child: Text('No events for this day'));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _selectedEvents.length,
      itemBuilder: (context, index) {
        final event = _selectedEvents[index];
        return _buildEventCard(event);
      },
    );
  }

  Widget _buildEventCard(CalendarEvent event) {
    final bool isMedication = event.type == EventType.medication;
    final bool isCompleted = event.status == EventStatus.completed ||
        event.status == EventStatus.taken;

    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: event.getEventColor().withAlpha(51),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(event.getEventIcon(), color: event.getEventColor()),
        ),
        title: Text(
          event.title,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text(event.time),
        trailing: isCompleted
            ? Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 8,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: Colors.green.withAlpha(26),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'Taken',
                  style: TextStyle(
                    color: Colors.green,
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              )
            : isMedication
                ? Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon:
                            const Icon(Icons.check_circle, color: Colors.green),
                        onPressed: () =>
                            _updateEventStatus(event, EventStatus.taken),
                      ),
                      IconButton(
                        icon: const Icon(Icons.cancel, color: Colors.red),
                        onPressed: () =>
                            _updateEventStatus(event, EventStatus.skipped),
                      ),
                    ],
                  )
                : IconButton(
                    icon: const Icon(Icons.check_circle, color: Colors.green),
                    onPressed: () =>
                        _updateEventStatus(event, EventStatus.completed),
                  ),
      ),
    );
  }

  Future<void> _updateEventStatus(
    CalendarEvent event,
    EventStatus status,
  ) async {
    try {
      await _calendarService.updateEventStatus(event.id, status);

      // If this is a medication event, also update the medication status using the service
      if (event.type == EventType.medication && event.relatedId != null) {
        await _calendarService.updateMedicationStatusFromEvent(
            event.relatedId!, status);
      }

      // Refresh events
      _fetchEvents();

      // Show success message
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Event marked as ${status.toString().split('.').last}',
            ),
          ),
        );
      }
    } catch (e) {
      // Show error message
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error updating event: $e')));
      }
    }
  }
}
