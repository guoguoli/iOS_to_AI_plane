//
//  ContentView.swift
//  CombineVsSSE
//
//  Created by 李果洲 on 2026/4/23.
//

import SwiftUI
import Combine
struct ContentView: View {
    var body: some View {
        VStack {
            Image(systemName: "globe")
                .imageScale(.large)
                .foregroundStyle(.tint)
            Text("Hello, world!")
        }
        .padding()
    }
}

class StreamViewModel: ObservableObject {
    @Published var displayedText: String = "哈哈哈"
    @Published var isLoading: Bool = true
    
    private var cancellables = Set<AnyCancellable>()
    
    // 对比1：Generator 和 Publisher
    // Python Generator  →  Swift Publisher (发布者)
    // for loop          →  sink/receive (订阅者)
    
    func streamText(from textPublisher: AnyPublisher<String, Never>) {
        textPublisher
            .receive(on: DispatchQueue.main)  // 主线程更新UI
            .sink { [weak self] newText in
                self?.displayedText += newText
            }
            .store(in: &cancellables)
    }
}

struct StreamTextView: View {
    @StateObject private var viewModel = StreamViewModel()
    
    var body: some View {
        VStack(alignment: .leading) {
            Text(viewModel.displayedText)
                .font(.body)
                .padding()
            
            if viewModel.isLoading {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle())
            }
        }
    }
}


class StreamService {
    // iOS 原生 SSE 实现
    func fetchStream(url: URL) -> AnyPublisher<String, Error> {
        var request = URLRequest(url: url)
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.setValue("no-cache", forHTTPHeaderField: "Cache-Control")
        
        return URLSession.shared.dataTaskPublisher(for: request)
            .tryMap { data, response -> String in
                guard let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode == 200 else {
                    throw URLError(.badServerResponse)
                }
                return String(data: data, encoding: .utf8) ?? ""
            }
            .eraseToAnyPublisher()
    }
}
#Preview {
    StreamTextView()
}
