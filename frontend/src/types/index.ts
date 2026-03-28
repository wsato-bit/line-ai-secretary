// ===== User =====
export type UserRole = 'guest' | 'user' | 'admin';
export type UserStatus = 'pending' | 'approved' | 'rejected' | 'disabled';

export interface User {
  id: string;
  lineUserId: string;
  lineDisplayName: string;
  linePictureUrl?: string;
  role: UserRole;
  status: UserStatus;
  appliedAt?: string;
  approvedAt?: string;
  lastActiveAt?: string;
  createdAt: string;
}

// ===== Memo =====
export type ContentType = 'text' | 'image' | 'url';

export interface Memo {
  id: string;
  content: string;
  contentType: ContentType;
  categoryId?: string;
  tags: string[];
  imageUrl?: string;
  imageOcrText?: string;
  url?: string;
  urlTitle?: string;
  urlSummary?: string;
  urlThumbnail?: string;
  isDeleted: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface MemoCategory {
  id: string;
  name: string;
  sortOrder: number;
  isDefault: boolean;
}

// ===== Email =====
export type EmailFilterType = 'sender' | 'domain' | 'subject_pattern';
export type EmailFilterAction = 'important' | 'exclude';
export type EmailCategory = 'important' | 'reference' | 'excluded';

export interface EmailFilter {
  id: string;
  filterType: EmailFilterType;
  filterValue: string;
  action: EmailFilterAction;
}

export interface EmailSummary {
  id: string;
  from: string;
  subject: string;
  summary: string;
  category: EmailCategory;
  receivedAt: string;
}

// ===== Schedule =====
export type EventType = 'business' | 'private';
export type EventVisibility = 'public' | 'private';
export type EventStatus = 'confirmed' | 'tentative';

export interface CalendarEvent {
  id: string;
  title: string;
  startDatetime: string;
  endDatetime: string;
  location?: string;
  eventType: EventType;
  visibility: EventVisibility;
  status: EventStatus;
  description?: string;
  colorId?: string;
}

export interface AvailableSlot {
  start: string;
  end: string;
  durationMinutes: number;
  prevEvent?: CalendarEvent;
  nextEvent?: CalendarEvent;
}

// ===== Unreplied =====
export interface UnrepliedItem {
  id: string;
  contactName: string;
  contentMemo?: string;
  registeredAt: string;
  completedAt?: string;
  isCompleted: boolean;
  daysElapsed: number;
}

// ===== EventColorRule =====
export interface EventColorRule {
  id: string;
  eventType: EventType;
  confirmationStatus: EventStatus;
  colorId: string;
  colorLabel?: string;
}

// ===== NotificationSetting =====
export interface NotificationSetting {
  id: string;
  morningSummaryTime: string;
  morningSummaryEnabled: boolean;
  reminderIntervals: number[];
  unrepliedThresholdDays: number;
  unrepliedReminderEnabled: boolean;
}

// ===== SSE Events =====
export type SSEEventType = 'text' | 'tool_start' | 'tool_end' | 'approval_request' | 'error' | 'done';

export interface SSEEvent {
  type: SSEEventType;
  data: Record<string, unknown>;
}
