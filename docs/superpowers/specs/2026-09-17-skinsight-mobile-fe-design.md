# Technical Design Specification: SkinSight Mobile Frontend (React Native)

- **Date:** 2026-09-17
- **Author:** Antigravity AI
- **Repository Path:** `D:\my-project\SkinSight(fe)`
- **Backend API Repository:** `D:\my-projects\SkinCareIn`
- **Design Mockups Source:** `C:\Users\wahid\Downloads\skinsight`
- **Target Platform:** Android (Android Studio Native Gradle build / Emulator & Device) + Cross-platform React Native

---

## 1. Executive Summary & Goals

SkinSight Mobile is an AI-powered personalized skincare assistant application for Android and iOS. This document defines the architectural specification for scaffolding and implementing the mobile client repository located at `D:\my-project\SkinSight(fe)`.

The client communicates with the existing FastAPI backend (`SkinCareIn`) and implements pixel-accurate mobile user interfaces derived from the high-fidelity mockups in `C:\Users\wahid\Downloads\skinsight`.

### Primary Objectives:
1. **Scaffold Clean Mobile Repository:** Set up React Native with TypeScript and prebuilt native `android/` directory that can be opened and run directly in Android Studio (`D:\ngoding\android`).
2. **Implement Feature-First Architecture:** Modular structure dividing the application by business domain (Auth, Onboarding, Dashboard, Products, Scan, Profile).
3. **Reproduce Figma Mockups Accurately:**
   - `Login.png` & `Sign Up.png`: Authentication, form validation, 6-digit OTP verification, and password reset flows.
   - `Assesment diri.png`: 5-step interactive skin assessment wizard.
   - `Dashboard.png`: Tab navigation with custom floating center action button, live routine checklist, UV index widget, personalized product carousels, and news feed.
   - `Scan Skin Type.png`: Camera viewfinder interface, face detection guideline overlay, and skin condition percentage breakdown.
   - `Product.png`: Searchable product catalog, multi-filter pills, product detail, harmful ingredients & irritancy analysis card, and side-by-side product comparison.
   - `Profile.png`: User profile management, skin type summary, scan history, and account settings.
4. **Resilient Data & API Layer:**
   - Standardized API configuration pointing to `http://localhost:8000/api/v1` with configurable override.
   - Zustand stores with AsyncStorage persistence for auth tokens and daily routines.
   - Graceful offline fallback with mock data so developers can inspect and verify all UI screens in Android Studio without requiring backend services to be running.

---

## 2. Technology Stack & Tooling

| Layer | Technology | Specification / Version |
|---|---|---|
| **Framework** | React Native (Expo Bare Workflow) | SDK 52+ with TypeScript |
| **Native Tooling** | Android Studio / Gradle | Bundled JBR (`D:\ngoding\android\jbr`), Android SDK (`C:\Users\wahid\AppData\Local\Android\Sdk`) |
| **Navigation** | React Navigation v7 | `@react-navigation/native`, `@react-navigation/native-stack`, `@react-navigation/bottom-tabs` |
| **Styling** | React Native StyleSheet | Modular theme tokens (`colors`, `typography`, `spacing`, `shadows`) |
| **State Management** | Zustand | Lightweight atomic stores with `persist` middleware |
| **Storage** | AsyncStorage | `@react-native-async-storage/async-storage` for tokens & cached state |
| **HTTP Client** | Axios | Interceptors for Bearer token injection and error handling |
| **Icons & Media** | `@expo/vector-icons` & Lucide icons | Feather / Ionicons / MaterialCommunityIcons |
| **Camera & Visuals** | `expo-camera` / placeholder simulator | Viewfinder and face analysis mockup overlay |

---

## 3. Directory & File Organization

The project at `D:\my-project\SkinSight(fe)` follows a feature-first modular structure:

```text
D:\my-project\SkinSight(fe)\
├── android/                   # Generated native Android project for Android Studio
├── assets/                    # App icons, splash screens, mockup asset images
│   ├── icons/
│   └── images/
├── src/
│   ├── components/            # Shared, reusable UI building blocks
│   │   ├── common/
│   │   │   ├── AppButton.tsx
│   │   │   ├── AppTextInput.tsx
│   │   │   ├── AppCard.tsx
│   │   │   ├── AppBadge.tsx
│   │   │   ├── AppHeader.tsx
│   │   │   ├── ProgressBar.tsx
│   │   │   ├── RoutineCard.tsx
│   │   │   ├── ProductCard.tsx
│   │   │   └── SafetyBadge.tsx
│   │   └── layout/
│   │       ├── ScreenContainer.tsx
│   │       └── FloatingScanButton.tsx
│   ├── constants/             # Design system tokens and app configuration
│   │   ├── theme.ts           # Colors, typography, spacing, border radii
│   │   └── config.ts          # API Base URL, storage keys, environment defaults
│   ├── features/              # Business domain modules
│   │   ├── auth/              # Login, SignUp, OtpVerification, ForgotPassword
│   │   │   ├── screens/
│   │   │   │   ├── LoginScreen.tsx
│   │   │   │   ├── SignUpScreen.tsx
│   │   │   │   ├── OtpVerificationScreen.tsx
│   │   │   │   └── ForgotPasswordScreen.tsx
│   │   │   └── types.ts
│   │   ├── onboarding/        # 5-step Skin Assessment Wizard
│   │   │   ├── screens/
│   │   │   │   ├── AssessmentWizardScreen.tsx
│   │   │   │   └── AssessmentCompleteScreen.tsx
│   │   │   └── types.ts
│   │   ├── dashboard/         # Home Tab
│   │   │   ├── screens/
│   │   │   │   └── HomeScreen.tsx
│   │   │   └── components/
│   │   │       ├── UvIndexCard.tsx
│   │   │       ├── RoutineSection.tsx
│   │   │       └── RecommendedCarousel.tsx
│   │   ├── products/          # Product Catalog, Detail, Analysis, Compare
│   │   │   ├── screens/
│   │   │   │   ├── ProductCatalogScreen.tsx
│   │   │   │   ├── ProductDetailScreen.tsx
│   │   │   │   ├── IngredientAnalysisScreen.tsx
│   │   │   │   └── ProductComparisonScreen.tsx
│   │   │   └── components/
│   │   │       ├── BrandFilterPills.tsx
│   │   │       └── CategoryTabs.tsx
│   │   ├── scan/              # Camera Face Scanner & Skin Analysis
│   │   │   ├── screens/
│   │   │   │   ├── SkinScanScreen.tsx
│   │   │   │   └── ScanResultScreen.tsx
│   │   │   └── components/
│   │   │       └── FaceOverlayFrame.tsx
│   │   ├── explore/           # Skincare News & Education
│   │   │   └── screens/
│   │   │       ├── ExploreScreen.tsx
│   │   │       └── ArticleDetailScreen.tsx
│   │   └── profile/           # User Profile & Settings
│   │       └── screens/
│   │           ├── ProfileScreen.tsx
│   │           ├── SkinProfileSummaryScreen.tsx
│   │           └── UpdatePasswordScreen.tsx
│   ├── navigation/            # Navigation routing definitions
│   │   ├── RootNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   ├── OnboardingNavigator.tsx
│   │   ├── MainTabNavigator.tsx
│   │   └── types.ts
│   ├── services/              # API networking and data sources
│   │   ├── api.ts             # Axios client with interceptors
│   │   ├── authService.ts
│   │   ├── dashboardService.ts
│   │   ├── productService.ts
│   │   ├── newsService.ts
│   │   └── mockData.ts        # Comprehensive offline fallback fixtures
│   ├── store/                 # Zustand state stores
│   │   ├── useAuthStore.ts
│   │   ├── useProductStore.ts
│   │   └── useRoutineStore.ts
│   └── types/                 # Shared data models & TypeScript interfaces
│       ├── user.ts
│       ├── product.ts
│       ├── routine.ts
│       └── news.ts
├── App.tsx                    # Application entry point with Providers
├── index.js                   # React Native registerRootComponent
├── app.json                   # Expo / Android app metadata configuration
├── package.json
├── tsconfig.json
└── README.md                  # Android Studio execution instructions
```

---

## 4. Design System & Theme Tokens (`src/constants/theme.ts`)

Extracted directly from the UI mockups in `C:\Users\wahid\Downloads\skinsight`:

### 4.1 Color Palette
```typescript
export const Colors = {
  // Brand Accents
  primary: '#3B82F6',        // Sky / Ocean Blue primary
  primaryDark: '#1D4ED8',    // Deep blue hover/press
  primaryLight: '#EFF6FF',   // Tint background for active chips & highlights
  accent: '#06B6D4',         // Cyan secondary accent

  // Neutrals & Surfaces
  background: '#FFFFFF',     // Clean pure white canvas
  surface: '#F8FAFC',        // Soft grey card background
  surfaceSecondary: '#F1F5F9', // Subtle contrast surface for pills/inputs
  border: '#E2E8F0',         // Divider & outline border
  borderFocus: '#3B82F6',    // Input active border

  // Text Hierarchy
  textPrimary: '#0F172A',    // Dark slate headings & labels
  textSecondary: '#64748B',  // Muted slate descriptions & hints
  textDisabled: '#94A3B8',   // Disabled state text
  textInverse: '#FFFFFF',    // White text on colored surfaces

  // Semantic Status
  success: '#10B981',        // Emerald green for OTP verified & routine checks
  successLight: '#ECFDF5',   // Green container background
  warning: '#F59E0B',        // Amber for moderate UV / cautionary ingredients
  warningLight: '#FFFBEB',
  danger: '#EF4444',         // Red alert for harmful / irritant ingredients
  dangerLight: '#FEF2F2',
};
```

### 4.2 Spacing & Radii
- **Spacing:** `xs: 4`, `sm: 8`, `md: 12`, `lg: 16`, `xl: 20`, `xxl: 24`, `xxxl: 32`
- **Border Radii:** `sm: 8`, `md: 12`, `lg: 16`, `xl: 24`, `full: 9999`
- **Shadows:** Subtle Android elevation (`elevation: 2` to `elevation: 6`) and iOS shadow offsets.

---

## 5. Screen Specifications & Flows

### 5.1 Authentication Flow (`features/auth`)
1. **LoginScreen (`Login.png`):**
   - Clean header with SkinSight logo and welcoming subtitle.
   - Email input with realtime email regex validation.
   - Password input with toggle visibility eye icon.
   - "Forgot Password?" clickable text link.
   - Primary "Sign In" button with loading indicator.
   - Bottom prompt: "Don't have an account? Sign Up".
2. **SignUpScreen (`Sign Up.png`):**
   - Full Name, Email, Password, and Confirm Password fields.
   - Password strength guidelines.
   - Terms & Privacy checkbox.
   - Primary "Sign Up" button navigating to OTP verification.
3. **OtpVerificationScreen:**
   - 6-digit PIN boxes with automatic focus shifting.
   - Resend code countdown timer (60s).
   - Verification success modal with green checkmark redirecting to Onboarding.
4. **ForgotPasswordScreen:**
   - Email submission to receive password reset link or verification code.

### 5.2 5-Step Skin Assessment Wizard (`features/onboarding`)
Matches `Assesment diri.png` layout:
- **Persistent Header:** 5-step progress bar (20% increments) with back button and skip option.
- **Step 1 (Demographics):** Gender selection cards (Female, Male, Rather not say) and Date of Birth picker.
- **Step 2 (Skin Concerns):** Multi-select interactive pills (Acne, Large Pores, Dark Spots, Redness, Dullness, Aging, Uneven Texture).
- **Step 3 (Skin Goals):** Multi-select goals (Clear Acne, Anti-aging, Hydration, Oil Control, Brightening, Stronger Skin Barrier).
- **Step 4 (Skin Type):** Single-select cards with descriptions (Oily, Dry, Normal, Combination, Sensitive) + shortcut button "Don't know? Scan your skin with AI".
- **Step 5 (Sensitive Ingredients):** Checkbox options for ingredients to avoid (Fragrance, Alcohol, Parabens, Sulfates, Essential Oils, Silicones).
- **Assessment Completed:** Celebration screen with confetti graphic, detected skin profile summary, and "Enter SkinSight" CTA.

### 5.3 Main Tab Navigation (`navigation/MainTabNavigator.tsx`)
Matches `Dashboard.png`:
- Custom bottom bar with 4 tabs and an elevated center circular Floating Action Button:
  1. **Home Tab (`HomeScreen.tsx`):**
     - Greeting header with user avatar and date.
     - Live UV Index card with current UV rating, risk category (Low/Moderate/High), and sunscreen reminder.
     - Morning & Night Daily Routine checklist cards with interactive checkboxes.
     - "Recommended For You" horizontal product carousel filtered by user's skin type.
     - "Latest Skincare News" cards linking to articles.
  2. **Product Catalog Tab (`ProductCatalogScreen.tsx`):**
     - Search bar with instant query filtering.
     - Brand selector pills (Azarine, Somethinc, Skintific, Wardah, Avoskin, Cosrx, etc.).
     - Category pills (Cleanser, Toner, Serum, Moisturizer, Sunscreen).
     - 2-column responsive product card grid showing thumbnail, brand name, product name, price in IDR format (`Rp 129.000`), and bookmark button.
  3. **Center Scan Button (Floating FAB):**
     - Elevated circular blue button with camera icon.
     - Opens `SkinScanScreen.tsx` (`Scan Skin Type.png`) with camera viewfinder, animated scanning radar, facial landmarks boundary, and instant analysis breakdown.
  4. **Explore Tab (`ExploreScreen.tsx`):**
     - Skincare News feed and Skincare Education guides/articles.
  5. **Profile Tab (`ProfileScreen.tsx`):**
     - User card with avatar, name, email, and skin type badge.
     - Action rows: Edit Profile, Skin Assessment Results, Saved Products, Scan History, Security/Password, Sign Out.

### 5.4 Product Detail, Ingredient Analysis & Comparison (`features/products`)
Matches `Product.png`:
- **ProductDetailScreen:**
  - Hero image banner with back and share buttons.
  - Brand name, product title, user rating stars, and price tag.
  - Skin type match badge (e.g. "98% Match for Oily Skin").
  - Description tab and full chemical ingredient list.
  - Fixed bottom bar with "Analyze Ingredients" and "Compare" actions.
- **IngredientAnalysisScreen:**
  - Safety score ring meter.
  - Harmful / Irritant ingredient warnings highlighted in red container.
  - Beneficial active ingredients highlighted with benefits (e.g. Niacinamide: Brightening & Pore reduction).
- **ProductComparisonScreen:**
  - Side-by-side comparison table comparing two products across: Price, Key Actives, Suitable Skin Types, and Irritancy rating.

---

## 6. State Management Architecture (Zustand)

### 6.1 `useAuthStore`
```typescript
interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isOnboarded: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  verifyOtp: (email: string, code: string) => Promise<boolean>;
  completeOnboarding: (data: AssessmentData) => Promise<void>;
  logout: () => Promise<void>;
}
```
- Uses `persist` middleware with `AsyncStorage` under key `@skinsight_auth`.

### 6.2 `useProductStore`
```typescript
interface ProductState {
  products: Product[];
  filteredProducts: Product[];
  favorites: string[]; // product IDs
  selectedBrand: string;
  selectedCategory: string;
  searchQuery: string;
  isLoading: boolean;
  fetchProducts: () => Promise<void>;
  setSearchQuery: (query: string) => void;
  setSelectedBrand: (brand: string) => void;
  setSelectedCategory: (category: string) => void;
  toggleFavorite: (productId: string) => void;
}
```

### 6.3 `useRoutineStore`
```typescript
interface RoutineState {
  morningCompleted: Record<string, boolean>; // id -> checked
  nightCompleted: Record<string, boolean>;
  toggleMorningItem: (id: string) => void;
  toggleNightItem: (id: string) => void;
  resetDaily: () => void;
}
```

---

## 7. Networking & API Configuration (`src/constants/config.ts`)

- **Standard Base URL:** `http://localhost:8000/api/v1` (configurable via `process.env.EXPO_PUBLIC_API_URL`).
- **Axios Interceptors:**
  - Automatically attaches `Authorization: Bearer ${token}` from `useAuthStore`.
  - On network connection error: gracefully returns mock data fixtures from `src/services/mockData.ts` to ensure flawless UI presentation and inspection during design verification.

---

## 8. Android Studio Run & Build Verification

The repository at `D:\my-project\SkinSight(fe)` provides a standard native Android Gradle setup:
1. **Open in Android Studio:**
   - Launch Android Studio from `D:\ngoding\android\bin\studio64.exe`.
   - Select **File > Open**, navigate to `D:\my-project\SkinSight(fe)\android`, and click **OK**.
   - Android Studio will synchronize the Gradle project using the preconfigured Java JBR (`D:\ngoding\android\jbr`) and SDK (`C:\Users\wahid\AppData\Local\Android\Sdk`).
2. **Terminal Execution:**
   - `npm run start` — Starts Metro development server.
   - `npm run android` — Builds debug APK and runs on the active Android emulator or connected device.
   - `npm test` — Executes test suites.

---

## 9. Verification & Acceptance Criteria

1. **Repository Structure:**
   - `D:\my-project\SkinSight(fe)` is fully scaffolded with TypeScript, valid `package.json`, and clean directory structure.
   - Native `android/` directory is present and valid for Android Studio opening.
2. **Mockup Fidelity:**
   - All 6 core screens and modals match the layout, typography, colors, and components from `C:\Users\wahid\Downloads\skinsight`.
3. **Interactive Navigation:**
   - Switching between tabs works smoothly.
   - Center floating scan button triggers camera scan screen.
   - Onboarding 5-step wizard transitions through steps and completes profile.
   - Product catalog filter pills and search bar filter the product grid dynamically.
4. **Resilience & Documentation:**
   - Clear `README.md` in `D:\my-project\SkinSight(fe)` explaining step-by-step how to open and run in Android Studio.
   - No TypeScript or build lint errors.
