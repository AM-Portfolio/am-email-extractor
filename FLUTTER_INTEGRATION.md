# Flutter Integration Guide

## 📱 Integrating Gmail Extractor API with Flutter App

This guide shows your Flutter teammate how to integrate the Gmail Extractor API into the main investment UI.

---

## 🔧 Prerequisites

Your Flask backend API will be available at:
- **Development:** `http://localhost:8080`
- **Production:** `https://api.munish.org/am/gmail` (via nginx proxy)

---

## 📦 1. Add Dependencies to `pubspec.yaml`

```yaml
dependencies:
  dio: ^5.4.0
  retrofit: ^4.0.3
  json_annotation: ^4.8.1
  url_launcher: ^6.2.2  # For opening OAuth URLs

dev_dependencies:
  retrofit_generator: ^8.0.4
  build_runner: ^2.4.6
  json_serializable: ^6.7.1
```

---

## 🗂️ 2. Create Data Models

### `lib/features/gmail/data/models/gmail_status_response.dart`

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'gmail_status_response.freezed.dart';
part 'gmail_status_response.g.dart';

@freezed
class GmailStatusResponse with _$GmailStatusResponse {
  const factory GmailStatusResponse({
    required bool connected,
    String? email,
    String? name,
  }) = _GmailStatusResponse;

  factory GmailStatusResponse.fromJson(Map<String, dynamic> json) =>
      _$GmailStatusResponseFromJson(json);
}
```

### `lib/features/gmail/data/models/holdings_response.dart`

```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'holdings_response.freezed.dart';
part 'holdings_response.g.dart';

@freezed
class HoldingsResponse with _$HoldingsResponse {
  const factory HoldingsResponse({
    required bool success,
    required String broker,
    required int count,
    required List<Holding> holdings,
    HoldingsMetadata? metadata,
  }) = _HoldingsResponse;

  factory HoldingsResponse.fromJson(Map<String, dynamic> json) =>
      _$HoldingsResponseFromJson(json);
}

@freezed
class Holding with _$Holding {
  const factory Holding({
    required String symbol,
    required double quantity,
    double? avgPrice,
    double? currentPrice,
    double? totalValue,
  }) = _Holding;

  factory Holding.fromJson(Map<String, dynamic> json) =>
      _$HoldingFromJson(json);
}

@freezed
class HoldingsMetadata with _$HoldingsMetadata {
  const factory HoldingsMetadata({
    String? emailSubject,
    String? emailDate,
    String? filename,
  }) = _HoldingsMetadata;

  factory HoldingsMetadata.fromJson(Map<String, dynamic> json) =>
      _$HoldingsMetadataFromJson(json);
}
```

---

## 🌐 3. Create API Client (Retrofit)

### `lib/features/gmail/data/datasources/gmail_remote_datasource.dart`

```dart
import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';
import '../models/gmail_status_response.dart';
import '../models/holdings_response.dart';

part 'gmail_remote_datasource.g.dart';

@RestApi(baseUrl: "http://localhost:8080/api/v1")
abstract class GmailApiClient {
  factory GmailApiClient(Dio dio, {String baseUrl}) = _GmailApiClient;

  @GET("/health")
  Future<Map<String, dynamic>> healthCheck();

  @GET("/gmail/connect")
  Future<Map<String, dynamic>> connectGmail(
    @Header("Authorization") String authorization,
  );

  @GET("/gmail/status")
  Future<GmailStatusResponse> checkStatus(
    @Header("Authorization") String authorization,
  );

  @DELETE("/gmail/disconnect")
  Future<Map<String, dynamic>> disconnectGmail(
    @Header("Authorization") String authorization,
  );

  @GET("/extract/gmail/{broker}")
  Future<HoldingsResponse> extractFromGmail(
    @Path("broker") String broker,
    @Query("pan") String pan,
    @Header("Authorization") String authorization,
  );

  @MultiPart()
  @POST("/extract/upload/{broker}")
  Future<HoldingsResponse> extractFromUpload(
    @Path("broker") String broker,
    @Part(name: "file") MultipartFile file,
    @Part(name: "password") String password,
    @Header("Authorization") String authorization,
  );
}
```

### `lib/features/gmail/data/datasources/gmail_remote_datasource_impl.dart`

```dart
import 'package:dio/dio.dart';
import 'gmail_remote_datasource.dart';
import '../models/gmail_status_response.dart';
import '../models/holdings_response.dart';

class GmailRemoteDataSourceImpl {
  final GmailApiClient _apiClient;
  final String Function() _getToken;  // Function to get JWT token

  GmailRemoteDataSourceImpl(this._apiClient, this._getToken);

  Future<Map<String, dynamic>> connectGmail() async {
    final token = _getToken();
    return await _apiClient.connectGmail("Bearer $token");
  }

  Future<GmailStatusResponse> checkStatus() async {
    final token = _getToken();
    return await _apiClient.checkStatus("Bearer $token");
  }

  Future<void> disconnectGmail() async {
    final token = _getToken();
    await _apiClient.disconnectGmail("Bearer $token");
  }

  Future<HoldingsResponse> fetchFromGmail(String broker, String pan) async {
    final token = _getToken();
    return await _apiClient.extractFromGmail(broker, pan, "Bearer $token");
  }

  Future<HoldingsResponse> uploadFile(
    String broker,
    String filePath,
    String password,
  ) async {
    final token = _getToken();
    final file = await MultipartFile.fromFile(filePath);
    return await _apiClient.extractFromUpload(
      broker,
      file,
      password,
      "Bearer $token",
    );
  }
}
```

---

## 🎯 4. Create Gmail OAuth Handler

### `lib/features/gmail/presentation/gmail_oauth_handler.dart`

```dart
import 'package:url_launcher/url_launcher.dart';
import '../data/datasources/gmail_remote_datasource_impl.dart';

class GmailOAuthHandler {
  final GmailRemoteDataSourceImpl _dataSource;

  GmailOAuthHandler(this._dataSource);

  /// Start Gmail OAuth flow
  Future<bool> connectGmail() async {
    try {
      // Step 1: Get auth URL from backend
      final response = await _dataSource.connectGmail();
      
      if (response['connected'] == true) {
        // Already connected
        return true;
      }
      
      final authUrl = response['auth_url'] as String?;
      if (authUrl == null) {
        throw Exception('No auth URL returned');
      }

      // Step 2: Open browser for OAuth
      final uri = Uri.parse(authUrl);
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
        throw Exception('Could not launch OAuth URL');
      }

      // Step 3: Backend handles callback automatically
      // You may want to poll checkStatus() to know when completed
      await _pollConnectionStatus();
      
      return true;
    } catch (e) {
      print('Gmail OAuth error: $e');
      return false;
    }
  }

  /// Poll connection status after OAuth
  Future<void> _pollConnectionStatus() async {
    for (int i = 0; i < 30; i++) {  // Poll for 30 seconds
      await Future.delayed(Duration(seconds: 1));
      
      final status = await _dataSource.checkStatus();
      if (status.connected) {
        return;
      }
    }
    throw Exception('OAuth timeout - user did not complete authorization');
  }

  /// Check current connection status
  Future<GmailStatusResponse> checkStatus() async {
    return await _dataSource.checkStatus();
  }

  /// Disconnect Gmail
  Future<void> disconnect() async {
    await _dataSource.disconnectGmail();
  }
}
```

---

## 🖼️ 5. Create UI Screens

### `lib/features/gmail/presentation/gmail_connection_page.dart`

```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'gmail_oauth_handler.dart';

class GmailConnectionPage extends ConsumerStatefulWidget {
  @override
  _GmailConnectionPageState createState() => _GmailConnectionPageState();
}

class _GmailConnectionPageState extends ConsumerState<GmailConnectionPage> {
  bool _isConnected = false;
  String? _email;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _checkStatus();
  }

  Future<void> _checkStatus() async {
    setState(() => _isLoading = true);
    
    try {
      // TODO: Get handler from provider
      final handler = ref.read(gmailOAuthHandlerProvider);
      final status = await handler.checkStatus();
      
      setState(() {
        _isConnected = status.connected;
        _email = status.email;
      });
    } catch (e) {
      print('Error checking status: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _connectGmail() async {
    setState(() => _isLoading = true);
    
    try {
      final handler = ref.read(gmailOAuthHandlerProvider);
      final success = await handler.connectGmail();
      
      if (success) {
        await _checkStatus();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gmail connected successfully')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to connect: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Gmail Connection')),
      body: Center(
        child: _isLoading
            ? CircularProgressIndicator()
            : _isConnected
                ? _buildConnectedView()
                : _buildDisconnectedView(),
      ),
    );
  }

  Widget _buildConnectedView() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.check_circle, color: Colors.green, size: 64),
        SizedBox(height: 16),
        Text('Gmail Connected', style: TextStyle(fontSize: 24)),
        SizedBox(height: 8),
        Text(_email ?? '', style: TextStyle(color: Colors.grey)),
        SizedBox(height: 32),
        ElevatedButton(
          onPressed: () async {
            final handler = ref.read(gmailOAuthHandlerProvider);
            await handler.disconnect();
            _checkStatus();
          },
          child: Text('Disconnect'),
          style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
        ),
      ],
    );
  }

  Widget _buildDisconnectedView() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.mail_outline, size: 64, color: Colors.grey),
        SizedBox(height: 16),
        Text('Connect your Gmail', style: TextStyle(fontSize: 24)),
        SizedBox(height: 8),
        Text(
          'Automatically import broker statements',
          style: TextStyle(color: Colors.grey),
        ),
        SizedBox(height: 32),
        ElevatedButton.icon(
          onPressed: _connectGmail,
          icon: Icon(Icons.link),
          label: Text('Connect Gmail'),
        ),
      ],
    );
  }
}
```

### `lib/features/gmail/presentation/fetch_from_gmail_widget.dart`

```dart
import 'package:flutter/material.dart';
import '../data/datasources/gmail_remote_datasource_impl.dart';

class FetchFromGmailWidget extends StatefulWidget {
  @override
  _FetchFromGmailWidgetState createState() => _FetchFromGmailWidgetState();
}

class _FetchFromGmailWidgetState extends State<FetchFromGmailWidget> {
  String _selectedBroker = 'groww';
  final _panController = TextEditingController();
  bool _isLoading = false;

  final List<Map<String, String>> _brokers = [
    {'id': 'groww', 'name': 'Groww'},
    {'id': 'zerodha', 'name': 'Zerodha'},
    {'id': 'angleone', 'name': 'AngelOne'},
    {'id': 'dhan', 'name': 'Dhan'},
    {'id': 'mstock', 'name': 'Mstock'},
  ];

  Future<void> _fetchHoldings() async {
    if (_panController.text.isEmpty && _selectedBroker != 'angleone') {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please enter PAN number')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      // TODO: Get data source from provider
      // final dataSource = ref.read(gmailDataSourceProvider);
      // final response = await dataSource.fetchFromGmail(
      //   _selectedBroker,
      //   _panController.text.toUpperCase(),
      // );
      
      // TODO: Navigate to results or update portfolio
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Holdings fetched successfully')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Fetch from Gmail', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            SizedBox(height: 16),
            
            // Broker dropdown
            DropdownButtonFormField<String>(
              value: _selectedBroker,
              decoration: InputDecoration(labelText: 'Select Broker'),
              items: _brokers.map((broker) {
                return DropdownMenuItem(
                  value: broker['id'],
                  child: Text(broker['name']!),
                );
              }).toList(),
              onChanged: (value) => setState(() => _selectedBroker = value!),
            ),
            SizedBox(height: 16),
            
            // PAN input
            if (_selectedBroker != 'angleone')
              TextField(
                controller: _panController,
                decoration: InputDecoration(
                  labelText: 'PAN Number',
                  hintText: 'ABCDE1234F',
                ),
                textCapitalization: TextCapitalization.characters,
                maxLength: 10,
              ),
            SizedBox(height: 16),
            
            // Fetch button
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _fetchHoldings,
              icon: _isLoading
                  ? SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(Icons.cloud_download),
              label: Text(_isLoading ? 'Fetching...' : 'Fetch Holdings'),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## 🔌 6. Setup Providers (Riverpod)

### `lib/features/gmail/providers/gmail_providers.dart`

```dart
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../data/datasources/gmail_remote_datasource.dart';
import '../data/datasources/gmail_remote_datasource_impl.dart';
import '../presentation/gmail_oauth_handler.dart';

// Dio instance with interceptor
final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8080/api/v1',  // Change for production
    connectTimeout: Duration(seconds: 30),
    receiveTimeout: Duration(seconds: 30),
  ));

  // Add logging interceptor
  dio.interceptors.add(LogInterceptor(requestBody: true, responseBody: true));

  return dio;
});

// API Client
final gmailApiClientProvider = Provider<GmailApiClient>((ref) {
  final dio = ref.watch(dioProvider);
  return GmailApiClient(dio);
});

// Token provider (gets JWT from secure storage)
final jwtTokenProvider = FutureProvider<String>((ref) async {
  const storage = FlutterSecureStorage();
  final token = await storage.read(key: 'jwt_token');
  if (token == null) throw Exception('Not authenticated');
  return token;
});

// Data Source
final gmailDataSourceProvider = Provider<GmailRemoteDataSourceImpl>((ref) {
  final apiClient = ref.watch(gmailApiClientProvider);
  
  String getToken() {
    // Synchronously get token from your auth state
    // This is a simplified example - adjust to your auth system
    final authState = ref.read(yourAuthStateProvider);
    return authState.token ?? '';
  }

  return GmailRemoteDataSourceImpl(apiClient, getToken);
});

// OAuth Handler
final gmailOAuthHandlerProvider = Provider<GmailOAuthHandler>((ref) {
  final dataSource = ref.watch(gmailDataSourceProvider);
  return GmailOAuthHandler(dataSource);
});
```

---

## ⚙️ 7. Configuration

### Update base URL for production

Create `lib/core/config/api_config.dart`:

```dart
class ApiConfig {
  static const bool isProduction = bool.fromEnvironment('dart.vm.product');
  
  static String get gmailApiBaseUrl {
    if (isProduction) {
      return 'https://api.munish.org/am/gmail';
    } else {
      return 'http://localhost:8080/api/v1';
    }
  }
}
```

Use this in `dioProvider`:
```dart
final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: ApiConfig.gmailApiBaseUrl,
    // ...
  ));
  return dio;
});
```

---

## 🔨 8. Generate Code

Run code generation:

```bash
flutter pub get
flutter pub run build_runner build --delete-conflicting-outputs
```

---

## ✅ 9. Testing

### Test health endpoint:

```dart
final response = await gmailApiClient.healthCheck();
print(response);  // Should print: {status: healthy, version: 1.0.0, ...}
```

### Test OAuth flow:

1. Navigate to Gmail connection page
2. Click "Connect Gmail"
3. Complete Google OAuth in browser
4. Verify status shows connected

### Test extraction:

```dart
final holdings = await gmailDataSource.fetchFromGmail('groww', 'ABCDE1234F');
print('${holdings.count} holdings fetched');
```

---

## 🚀 Production Checklist

- [ ] Update `ApiConfig.gmailApiBaseUrl` to production URL
- [ ] Configure nginx reverse proxy to route `/am/gmail/*` to backend
- [ ] Update Google OAuth redirect URIs in Google Cloud Console
- [ ] Test with real Gmail data
- [ ] Add error handling and retry logic
- [ ] Add loading states in UI

---

## 📞 Need Help?

Refer back to the backend API documentation in `/DOCKER_DEPLOYMENT.md` for endpoint details and troubleshooting.
