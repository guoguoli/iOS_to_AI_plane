//
//  HomeworkCheckerView.swift
//  HomeworkChecker
//
//  Created by 李果洲 on 2026/4/23.
//

import SwiftUI
import PhotosUI

// ============================================================
// iOS 作业批改助手
// ============================================================

struct HomeworkCheckerView: View {
    @StateObject private var viewModel = HomeworkCheckerViewModel()
    
    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                
                // 科目选择
                SubjectPicker(selectedSubject: $viewModel.selectedSubject)
                
                // 图片选择
                ImagePicker(image: $viewModel.selectedImage)
                
                // 预览
                if let image = viewModel.selectedImage {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFit()
                        .frame(height: 200)
                        .cornerRadius(12)
                }
                
                // 批改按钮
                Button(action: {
                    viewModel.checkHomework()
                }) {
                    HStack {
                        if viewModel.isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        } else {
                            Image(systemName: "checkmark.circle.fill")
                            Text("开始批改")
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(12)
                }
                .disabled(viewModel.selectedImage == nil || viewModel.isLoading)
                
                // 结果展示
                if let result = viewModel.result {
                    CorrectionResultView(result: result)
                }
                
                Spacer()
            }
            .padding()
            .navigationTitle("作业批改")
        }
    }
}

@MainActor
class HomeworkCheckerViewModel: ObservableObject {
    @Published var selectedSubject: Subject = .math
    @Published var selectedImage: UIImage?
    @Published var isLoading = false
    @Published var result: CorrectionResult?
    @Published var errorMessage: String?
    
    enum Subject: String, CaseIterable {
        case math = "math"
        case english = "english"
        
        var displayName: String {
            switch self {
            case .math: return "数学"
            case .english: return "英语"
            }
        }
    }
    
    func checkHomework() {
        guard let image = selectedImage else { return }
        
        isLoading = true
        
        // 转换为Base64
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            errorMessage = "图片处理失败"
            isLoading = false
            return
        }
        
        let base64String = imageData.base64EncodedString()
        
        // 调用API
        Task {
            do {
                let response = try await HomeworkAPIService.shared.checkHomework(
                    imageBase64: base64String,
                    subject: selectedSubject.rawValue
                )
                
                self.result = response
                self.isLoading = false
            } catch {
                self.errorMessage = error.localizedDescription
                self.isLoading = false
            }
        }
    }
}

struct CorrectionResult {
    let score: Int
    let feedback: String
    let explanation: String
    let relatedKnowledge: [String]
    let isCorrect: Bool
}

class HomeworkAPIService {
    static let shared = HomeworkAPIService()
    
    func checkHomework(imageBase64: String, subject: String) async throws -> CorrectionResult {
        let url = URL(string: "http://127.0.0.1:8000/api/check")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        let body: [String: Any] = [
            "image": imageBase64,
            "subject": subject,
            "student_name": "default",
            "grade": "unknown"
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(APIResponse.self, from: data)
        
        return CorrectionResult(
            score: response.score,
            feedback: response.feedback,
            explanation: response.explanation,
            relatedKnowledge: response.relatedKnowledge,
            isCorrect: response.success
        )
    }
}

struct APIResponse: Codable {
    let success: Bool
    let score: Int
    let feedback: String
    let explanation: String
    let relatedKnowledge: [String]
}

// ============================================================
// 辅助视图
// ============================================================

struct SubjectPicker: View {
    @Binding var selectedSubject: HomeworkCheckerViewModel.Subject
    
    var body: some View {
        Picker("科目", selection: $selectedSubject) {
            ForEach(HomeworkCheckerViewModel.Subject.allCases, id: \.self) { subject in
                Text(subject.displayName).tag(subject)
            }
        }
        .pickerStyle(SegmentedPickerStyle())
    }
}

struct ImagePicker: View {
    @Binding var image: UIImage?
    @State private var showingPicker = false
    
    var body: some View {
        Button(action: { showingPicker = true }) {
            HStack {
                Image(systemName: "photo.on.rectangle.angled")
                Text(image == nil ? "选择作业图片" : "重新选择")
            }
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color.gray.opacity(0.1))
            .cornerRadius(12)
        }
        .sheet(isPresented: $showingPicker) {
            ImagePickerView(image: $image)
        }
    }
}

struct ImagePickerView: UIViewControllerRepresentable {
    @Binding var image: UIImage?
    @Environment(\.dismiss) var dismiss
    
    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        config.filter = .images
        config.selectionLimit = 1
        
        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }
    
    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }
    
    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: ImagePickerView
        
        init(_ parent: ImagePickerView) {
            self.parent = parent
        }
        
        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            parent.dismiss()
            
            guard let provider = results.first?.itemProvider,
                  provider.canLoadObject(ofClass: UIImage.self) else { return }
            
            provider.loadObject(ofClass: UIImage.self) { image, _ in
                DispatchQueue.main.async {
                    self.parent.image = image as? UIImage
                }
            }
        }
    }
}

struct CorrectionResultView: View {
    let result: CorrectionResult
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // 分数展示
            HStack {
                Circle()
                    .fill(result.isCorrect ? Color.green : Color.orange)
                    .frame(width: 60, height: 60)
                    .overlay(
                        Text("\(result.score)")
                            .font(.title)
                            .fontWeight(.bold)
                            .foregroundColor(.white)
                    )
                
                VStack(alignment: .leading) {
                    Text(result.isCorrect ? "表现良好！" : "需要改进")
                        .font(.headline)
                    Text("总分 100 分")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
                
                Spacer()
            }
            
            Divider()
            
            // 评语
            VStack(alignment: .leading, spacing: 8) {
                Text("📝 总体评语")
                    .font(.headline)
                Text(result.feedback)
                    .font(.body)
            }
            
            // 讲解
            if !result.explanation.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("📚 错题讲解")
                        .font(.headline)
                    Text(result.explanation)
                        .font(.body)
                }
            }
            
            // 薄弱知识点
            if !result.relatedKnowledge.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("🎯 需要加强的知识点")
                        .font(.headline)
                    FlowLayout(spacing: 8) {
                        ForEach(result.relatedKnowledge, id: \.self) { topic in
                            Text(topic)
                                .font(.caption)
                                .padding(.horizontal, 12)
                                .padding(.vertical, 6)
                                .background(Color.blue.opacity(0.1))
                                .foregroundColor(.blue)
                                .cornerRadius(16)
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(radius: 4)
    }
}

// FlowLayout 用于流式布局标签
struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResult(in: proposal.width ?? 0, subviews: subviews, spacing: spacing)
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResult(in: bounds.width, subviews: subviews, spacing: spacing)
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.positions[index].x,
                                       y: bounds.minY + result.positions[index].y),
                         proposal: .unspecified)
        }
    }
    
    struct FlowResult {
        var size: CGSize = .zero
        var positions: [CGPoint] = []
        
        init(in maxWidth: CGFloat, subviews: Subviews, spacing: CGFloat) {
            var x: CGFloat = 0
            var y: CGFloat = 0
            var lineHeight: CGFloat = 0
            
            for subview in subviews {
                let size = subview.sizeThatFits(.unspecified)
                
                if x + size.width > maxWidth && x > 0 {
                    x = 0
                    y += lineHeight + spacing
                    lineHeight = 0
                }
                
                positions.append(CGPoint(x: x, y: y))
                lineHeight = max(lineHeight, size.height)
                x += size.width + spacing
                
                self.size.width = max(self.size.width, x)
            }
            
            self.size.height = y + lineHeight
        }
    }
}

#Preview {
    HomeworkCheckerView()
}
