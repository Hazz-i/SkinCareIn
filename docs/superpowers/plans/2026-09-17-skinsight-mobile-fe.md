# SkinSight Mobile Frontend (React Native) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold and implement the complete React Native mobile application at `D:\my-project\SkinSight(fe)`, targeting Android Studio execution and reproducing the UI mockups from `C:\Users\wahid\Downloads\skinsight` with feature-first architecture, Zustand state management, and backend API integration.

**Architecture:** Feature-first modular React Native application organized into domain modules (`auth`, `onboarding`, `dashboard`, `products`, `scan`, `explore`, `profile`). Uses React Navigation (stacks + bottom tabs + floating center scan action button), pure StyleSheet styling with centralized theme tokens, and an Axios networking layer with seamless offline mock fallback.

**Tech Stack:** React Native (Expo SDK 52 / TypeScript), Android Studio native Gradle build, Zustand, AsyncStorage, React Navigation v7, Jest + React Native Testing Library.

**Spec:** [`docs/superpowers/specs/2026-09-17-skinsight-mobile-fe-design.md`](file:///D:/my-projects/SkinCareIn/docs/superpowers/specs/2026-09-17-skinsight-mobile-fe-design.md)

## Global Constraints
- Target mobile directory: `D:\my-project\SkinSight(fe)`
- Target Android Studio install: `D:\ngoding\android`
- Android SDK path: `C:\Users\wahid\AppData\Local\Android\Sdk`
- Standard API Base URL: `http://localhost:8000/api/v1` (with no complex platform branching)
- Design mockups: `C:\Users\wahid\Downloads\skinsight` (Login, Sign Up, Assesment diri, Dashboard, Scan Skin Type, Product, Profile)
- Styling: Pure React Native `StyleSheet` with centralized tokens in `src/constants/theme.ts`
- State management: Zustand with AsyncStorage persistence
- All test suites must pass without errors (`npm test`, `npm run typecheck`)

---

### Task 1: Scaffold React Native Project Structure at `D:\my-project\SkinSight(fe)`

**Files:**
- Create: `D:\my-project\SkinSight(fe)\package.json`
- Create: `D:\my-project\SkinSight(fe)\tsconfig.json`
- Create: `D:\my-project\SkinSight(fe)\app.json`
- Create: `D:\my-project\SkinSight(fe)\index.js`
- Create: `D:\my-project\SkinSight(fe)\App.tsx`
- Create: `D:\my-project\SkinSight(fe)\.gitignore`
- Create: `D:\my-project\SkinSight(fe)\android\build.gradle`
- Create: `D:\my-project\SkinSight(fe)\android\settings.gradle`
- Create: `D:\my-project\SkinSight(fe)\android\app\build.gradle`
- Create: `D:\my-project\SkinSight(fe)\android\app\src\main\AndroidManifest.xml`
- Create: `D:\my-project\SkinSight(fe)\tests\setup.ts`
- Create: `D:\my-project\SkinSight(fe)\tests\app.test.tsx`

**Interfaces:**
- Consumes: None (root scaffold)
- Produces: Base React Native project structure runnable in Android Studio and verified via Jest

- [ ] **Step 1: Write the failing initial smoke test**

```typescript
// D:\my-project\SkinSight(fe)\tests\app.test.tsx
import React from 'react';
import { render } from '@testing-library/react-native';
import App from '../App';

describe('App Root', () => {
  it('renders root application successfully', () => {
    const { getByTestId } = render(<App />);
    expect(getByTestId('app-root')).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd "D:\my-project\SkinSight(fe)" && npm test`
Expected: FAIL (missing dependencies or files)

- [ ] **Step 3: Create directory structure, package.json, configs, and minimal App.tsx**

```json
// D:\my-project\SkinSight(fe)\package.json
{
  "name": "skinsight-mobile",
  "version": "1.0.0",
  "private": true,
  "main": "index.js",
  "scripts": {
    "start": "expo start",
    "android": "expo run:android",
    "typecheck": "tsc --noEmit",
    "test": "jest"
  },
  "dependencies": {
    "@react-native-async-storage/async-storage": "^1.23.1",
    "@react-navigation/bottom-tabs": "^7.2.0",
    "@react-navigation/native": "^7.0.14",
    "@react-navigation/native-stack": "^7.2.0",
    "axios": "^1.7.9",
    "expo": "~52.0.0",
    "expo-camera": "~16.0.17",
    "expo-status-bar": "~2.0.1",
    "react": "18.3.1",
    "react-native": "0.76.7",
    "react-native-safe-area-context": "4.12.0",
    "react-native-screens": "~4.4.0",
    "zustand": "^5.0.3"
  },
  "devDependencies": {
    "@babel/core": "^7.25.2",
    "@testing-library/react-native": "^13.0.1",
    "@types/jest": "^29.5.14",
    "@types/react": "~18.3.12",
    "jest": "^29.7.0",
    "typescript": "~5.3.3"
  }
}
```

```tsx
// D:\my-project\SkinSight(fe)\App.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

export default function App() {
  return (
    <SafeAreaProvider>
      <View testID="app-root" style={styles.container}>
        <Text style={styles.title}>SkinSight AI</Text>
      </View>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFFFF', justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 24, fontWeight: '700', color: '#3B82F6' },
});
```

- [ ] **Step 4: Create Android native folder structure for Android Studio**

Generate `android/settings.gradle`, `android/build.gradle`, `android/app/build.gradle`, and `android/app/src/main/AndroidManifest.xml` with standard SDK 34/35 properties configured to use `D:\ngoding\android\jbr` and `C:\Users\wahid\AppData\Local\Android\Sdk`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `npm test` & `npm run typecheck`
Expected: PASS

- [ ] **Step 6: Initialize git in `D:\my-project\SkinSight(fe)` and commit**

```bash
git init
git add .
git commit -m "chore: initial scaffold of skinsight mobile frontend"
```

---

### Task 2: Design System Theme, Constants & Shared UI Components

**Files:**
- Create: `D:\my-project\SkinSight(fe)\src\constants\theme.ts`
- Create: `D:\my-project\SkinSight(fe)\src\constants\config.ts`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\AppButton.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\AppTextInput.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\AppCard.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\AppBadge.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\AppHeader.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\ProgressBar.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\RoutineCard.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\ProductCard.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\components\common\SafetyBadge.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\utils\formatters.ts`
- Test: `D:\my-project\SkinSight(fe)\tests\components\common.test.tsx`
- Test: `D:\my-project\SkinSight(fe)\tests\utils\formatters.test.ts`

**Interfaces:**
- Consumes: None
- Produces: Reusable UI primitives (`AppButton`, `AppTextInput`, `ProgressBar`, `ProductCard`, etc.), formatters (`formatPriceIdr`, `getUvCategory`), and theme tokens (`Colors`, `Typography`, `Spacing`).

- [ ] **Step 1: Write the failing tests for formatters and common components**

```typescript
// D:\my-project\SkinSight(fe)\tests\utils\formatters.test.ts
import { formatPriceIdr, getUvCategory } from '../../src/utils/formatters';

describe('Formatters', () => {
  it('formats numbers into Indonesian Rupiah currency format', () => {
    expect(formatPriceIdr(129000)).toBe('Rp 129.000');
    expect(formatPriceIdr(0)).toBe('Rp 0');
  });

  it('determines UV risk category correctly', () => {
    expect(getUvCategory(2)).toEqual({ level: 'Low', color: '#10B981' });
    expect(getUvCategory(5)).toEqual({ level: 'Moderate', color: '#F59E0B' });
    expect(getUvCategory(8)).toEqual({ level: 'High', color: '#EF4444' });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test tests/utils/formatters.test.ts`
Expected: FAIL (Cannot find module)

- [ ] **Step 3: Implement `theme.ts`, `config.ts`, `formatters.ts`, and common UI components**

Implement `Colors`, `Spacing`, `Typography`, `formatPriceIdr`, `getUvCategory`, and the full set of reusable components matching Figma aesthetics (smooth corner radius, shadows, touchable feedback).

- [ ] **Step 4: Run tests and verify they pass**

Run: `npm test tests/utils/formatters.test.ts tests/components/common.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ tests/
git commit -m "feat: add design system tokens, formatters, and reusable UI components"
```

---

### Task 3: State Management (Zustand) & API Service Layer with Offline Mock Fallback

**Files:**
- Create: `D:\my-project\SkinSight(fe)\src\types\user.ts`
- Create: `D:\my-project\SkinSight(fe)\src\types\product.ts`
- Create: `D:\my-project\SkinSight(fe)\src\types\routine.ts`
- Create: `D:\my-project\SkinSight(fe)\src\types\news.ts`
- Create: `D:\my-project\SkinSight(fe)\src\services\mockData.ts`
- Create: `D:\my-project\SkinSight(fe)\src\services\api.ts`
- Create: `D:\my-project\SkinSight(fe)\src\services\authService.ts`
- Create: `D:\my-project\SkinSight(fe)\src\services\dashboardService.ts`
- Create: `D:\my-project\SkinSight(fe)\src\services\productService.ts`
- Create: `D:\my-project\SkinSight(fe)\src\store\useAuthStore.ts`
- Create: `D:\my-project\SkinSight(fe)\src\store\useProductStore.ts`
- Create: `D:\my-project\SkinSight(fe)\src\store\useRoutineStore.ts`
- Test: `D:\my-project\SkinSight(fe)\tests\store\useAuthStore.test.ts`
- Test: `D:\my-project\SkinSight(fe)\tests\store\useRoutineStore.test.ts`
- Test: `D:\my-project\SkinSight(fe)\tests\services\productService.test.ts`

**Interfaces:**
- Consumes: `theme.ts`, `config.ts`
- Produces: Stores (`useAuthStore`, `useProductStore`, `useRoutineStore`) and API services with seamless offline fallback fixtures.

- [ ] **Step 1: Write the failing tests for Zustand stores and service fallbacks**

```typescript
// D:\my-project\SkinSight(fe)\tests\store\useRoutineStore.test.ts
import { useRoutineStore } from '../../src/store/useRoutineStore';

describe('useRoutineStore', () => {
  beforeEach(() => {
    useRoutineStore.getState().resetDaily();
  });

  it('toggles morning and night routine checklist items', () => {
    expect(useRoutineStore.getState().morningCompleted['cleanser']).toBeFalsy();
    useRoutineStore.getState().toggleMorningItem('cleanser');
    expect(useRoutineStore.getState().morningCompleted['cleanser']).toBeTruthy();
    useRoutineStore.getState().toggleMorningItem('cleanser');
    expect(useRoutineStore.getState().morningCompleted['cleanser']).toBeFalsy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test tests/store/useRoutineStore.test.ts`
Expected: FAIL

- [ ] **Step 3: Implement models, mockData, api client, services, and Zustand stores**

Implement standard Axios client pointing to `http://localhost:8000/api/v1` with token header injection, comprehensive mock fixtures for offline testing in Android Studio, and Zustand stores.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/store/ tests/services/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ tests/
git commit -m "feat: add zustand stores and api services with offline mock fallback"
```

---

### Task 4: Authentication & 5-Step Skin Assessment Onboarding

**Files:**
- Create: `D:\my-project\SkinSight(fe)\src\features\auth\screens\LoginScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\auth\screens\SignUpScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\auth\screens\OtpVerificationScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\auth\screens\ForgotPasswordScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\onboarding\screens\AssessmentWizardScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\onboarding\screens\AssessmentCompleteScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\navigation\AuthNavigator.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\navigation\OnboardingNavigator.tsx`
- Test: `D:\my-project\SkinSight(fe)\tests\features\auth\LoginScreen.test.tsx`
- Test: `D:\my-project\SkinSight(fe)\tests\features\onboarding\AssessmentWizard.test.tsx`

**Interfaces:**
- Consumes: `useAuthStore`, `AppButton`, `AppTextInput`, `ProgressBar`
- Produces: `AuthNavigator` and `OnboardingNavigator` handling user authentication and 5-step skin profile creation.

- [ ] **Step 1: Write the failing tests for LoginScreen validation and AssessmentWizard steps**

```typescript
// D:\my-project\SkinSight(fe)\tests\features\auth\LoginScreen.test.tsx
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import LoginScreen from '../../../src/features/auth/screens/LoginScreen';

describe('LoginScreen', () => {
  it('validates email format and displays error message for invalid input', () => {
    const { getByPlaceholderText, getByText } = render(<LoginScreen navigation={{} as any} />);
    const emailInput = getByPlaceholderText('Enter your email');
    fireEvent.changeText(emailInput, 'invalid-email');
    fireEvent.press(getByText('Sign In'));
    expect(getByText(/invalid email format/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test tests/features/auth/LoginScreen.test.tsx`
Expected: FAIL

- [ ] **Step 3: Implement Auth screens and Onboarding wizard**

Implement `LoginScreen` (`Login.png`), `SignUpScreen` (`Sign Up.png`), `OtpVerificationScreen`, `ForgotPasswordScreen`, and `AssessmentWizardScreen` (`Assesment diri.png` with Gender/DOB, Skin Concerns, Goals, Skin Type, Avoided Ingredients, and completion celebration).

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/features/auth/ tests/features/onboarding/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ tests/
git commit -m "feat: implement auth screens and 5-step skin assessment onboarding wizard"
```

---

### Task 5: Dashboard & Main Tab Navigation with Custom Floating Action Button

**Files:**
- Create: `D:\my-project\SkinSight(fe)\src\components\layout\FloatingScanButton.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\dashboard\screens\HomeScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\dashboard\components\UvIndexCard.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\dashboard\components\RoutineSection.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\dashboard\components\RecommendedCarousel.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\scan\screens\SkinScanScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\scan\screens\ScanResultScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\scan\components\FaceOverlayFrame.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\explore\screens\ExploreScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\profile\screens\ProfileScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\navigation\MainTabNavigator.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\navigation\RootNavigator.tsx`
- Test: `D:\my-project\SkinSight(fe)\tests\features\dashboard\HomeScreen.test.tsx`
- Test: `D:\my-project\SkinSight(fe)\tests\features\scan\SkinScanScreen.test.tsx`

**Interfaces:**
- Consumes: `useAuthStore`, `useRoutineStore`, `useProductStore`, `RoutineCard`, `ProductCard`
- Produces: `RootNavigator` managing Auth -> Onboarding -> MainTabs transitions.

- [ ] **Step 1: Write the failing tests for HomeScreen and SkinScanScreen**

```typescript
// D:\my-project\SkinSight(fe)\tests\features\dashboard\HomeScreen.test.tsx
import React from 'react';
import { render } from '@testing-library/react-native';
import HomeScreen from '../../../src/features/dashboard/screens/HomeScreen';

describe('HomeScreen', () => {
  it('renders UV index card, daily routine checklist, and recommendations', () => {
    const { getByText } = render(<HomeScreen navigation={{} as any} />);
    expect(getByText(/UV Index/i)).toBeTruthy();
    expect(getByText(/Daily Routine/i)).toBeTruthy();
    expect(getByText(/Recommended for you/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test tests/features/dashboard/HomeScreen.test.tsx`
Expected: FAIL

- [ ] **Step 3: Implement Dashboard screens, Scan Viewfinder with face analysis breakdown, Explore, Profile, and MainTabNavigator with elevated FAB**

Build pixel-accurate UI matching `Dashboard.png`, `Scan Skin Type.png`, and `Profile.png`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/features/dashboard/ tests/features/scan/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ tests/
git commit -m "feat: implement dashboard home tab, camera skin scanner, and main tab navigation"
```

---

### Task 6: Product Catalog, Detail, Harmful Ingredient Analysis & Comparison

**Files:**
- Create: `D:\my-project\SkinSight(fe)\src\features\products\screens\ProductCatalogScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\products\screens\ProductDetailScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\products\screens\IngredientAnalysisScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\products\screens\ProductComparisonScreen.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\products\components\BrandFilterPills.tsx`
- Create: `D:\my-project\SkinSight(fe)\src\features\products\components\CategoryTabs.tsx`
- Modify: `D:\my-project\SkinSight(fe)\src\navigation\MainTabNavigator.tsx` (add product stack modals)
- Test: `D:\my-project\SkinSight(fe)\tests\features\products\ProductCatalog.test.tsx`
- Test: `D:\my-project\SkinSight(fe)\tests\features\products\ProductDetail.test.tsx`

**Interfaces:**
- Consumes: `useProductStore`, `ProductCard`, `SafetyBadge`, `AppButton`
- Produces: Complete product browsing, searching, ingredient safety inspection, and side-by-side comparison.

- [ ] **Step 1: Write the failing tests for product catalog filtering and search**

```typescript
// D:\my-project\SkinSight(fe)\tests\features\products\ProductCatalog.test.tsx
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import ProductCatalogScreen from '../../../src/features/products/screens/ProductCatalogScreen';

describe('ProductCatalogScreen', () => {
  it('filters product list when user types in search input', () => {
    const { getByPlaceholderText, queryByText } = render(<ProductCatalogScreen navigation={{} as any} />);
    const searchInput = getByPlaceholderText(/search skincare/i);
    fireEvent.changeText(searchInput, 'Azarine');
    expect(queryByText(/Azarine/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test tests/features/products/ProductCatalog.test.tsx`
Expected: FAIL

- [ ] **Step 3: Implement ProductCatalog, ProductDetail, IngredientAnalysis, and ProductComparison screens matching `Product.png`**

Implement search with brand pills (Azarine, Somethinc, Skintific, etc.), category tabs, 2-column grid, chemical ingredient safety list with irritancy ratings, and 2-product comparison table.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test tests/features/products/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ tests/
git commit -m "feat: implement product catalog, detail, ingredient analysis, and comparison screens"
```

---

### Task 7: App Integration, Android Studio Run Configuration & Documentation

**Files:**
- Modify: `D:\my-project\SkinSight(fe)\App.tsx` (integrate `RootNavigator`, SafeAreaProvider, StatusBar)
- Create: `D:\my-project\SkinSight(fe)\README.md` (Android Studio step-by-step launch & emulator guide)
- Modify: `D:\my-project\SkinSight(fe)\package.json` (ensure all scripts and test runners ready)
- Test: `D:\my-project\SkinSight(fe)\tests\app.test.tsx`

**Interfaces:**
- Consumes: `RootNavigator`, all feature screens
- Produces: Complete runnable mobile application ready for Android Studio inspection

- [ ] **Step 1: Write the failing full app integration test**

```typescript
// D:\my-project\SkinSight(fe)\tests\app.test.tsx
import React from 'react';
import { render } from '@testing-library/react-native';
import App from '../App';

describe('Full App Integration', () => {
  it('renders root navigation container and displays auth stack by default', () => {
    const { getByText } = render(<App />);
    expect(getByText(/SkinSight/i)).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test tests/app.test.tsx`
Expected: FAIL

- [ ] **Step 3: Connect App.tsx with RootNavigator and create comprehensive Android Studio README.md**

Document exact steps to open `D:\my-project\SkinSight(fe)\android` in Android Studio (`D:\ngoding\android`), configure SDK (`C:\Users\wahid\AppData\Local\Android\Sdk`), start Metro (`npm run start`), and run debug build (`npm run android` or Android Studio Run button).

- [ ] **Step 4: Run all test suites and TypeScript checks**

Run: `npm test` & `npm run typecheck`
Expected: All tests pass (0 failures), 0 TypeScript compilation errors.

- [ ] **Step 5: Commit**

```bash
git add App.tsx README.md package.json tests/
git commit -m "feat: complete app root integration, android studio setup guide, and tests"
```
