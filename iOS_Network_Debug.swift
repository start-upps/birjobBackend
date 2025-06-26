// Add this to your iOS app for better network debugging

import Network
import Foundation

class NetworkMonitor: ObservableObject {
    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "NetworkMonitor")
    
    @Published var isConnected = false
    @Published var connectionType: NWInterface.InterfaceType?
    
    init() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isConnected = path.status == .satisfied
                self?.connectionType = path.availableInterfaces.first?.type
                
                print("🌐 Network Status: \(path.status)")
                print("🌐 Interface Type: \(path.availableInterfaces.first?.type?.debugDescription ?? "None")")
            }
        }
        monitor.start(queue: queue)
    }
}

// API Service with better error handling
class APIService {
    static let shared = APIService()
    private let baseURL = "https://birjobbackend-ir3e.onrender.com"
    
    func testConnection() async {
        guard let url = URL(string: "\(baseURL)/api/v1/health") else { return }
        
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            
            if let httpResponse = response as? HTTPURLResponse {
                print("✅ Status Code: \(httpResponse.statusCode)")
                print("✅ Response: \(String(data: data, encoding: .utf8) ?? "No data")")
            }
        } catch {
            print("❌ Network Error: \(error.localizedDescription)")
            print("❌ Error Code: \((error as NSError).code)")
        }
    }
}

// URLRequest extension for debugging
extension URLRequest {
    func debugPrint() {
        print("🔍 URL: \(url?.absoluteString ?? "nil")")
        print("🔍 Method: \(httpMethod ?? "GET")")
        print("🔍 Headers: \(allHTTPHeaderFields ?? [:])")
        if let body = httpBody, let bodyString = String(data: body, encoding: .utf8) {
            print("🔍 Body: \(bodyString)")
        }
    }
}