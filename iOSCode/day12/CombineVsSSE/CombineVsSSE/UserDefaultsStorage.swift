//
//  UserDefaultsStorage.swift
//  CombineVsSSE
//
//  Created by 李果洲 on 2026/4/23.
//

import Foundation


// ============================================================
// iOS 端对话历史存储方案对比
// ============================================================

/*
┌─────────────────────────────────────────────────────────────────────┐
│                    iOS 存储方案对比                                    │
├──────────────────┬────────────────────────────────────────────────┤
│   存储方式        │                   适用场景                       │
├──────────────────┼────────────────────────────────────────────────┤
│ UserDefaults     │ 小数据、简单配置、会话ID存储                       │
├──────────────────┼────────────────────────────────────────────────┤
│ FileManager      │ 中等大小、JSON格式的对话历史                      │
├──────────────────┼────────────────────────────────────────────────┤
│ Core Data        │ 大量结构化数据、复杂查询、持久化                   │
├──────────────────┼────────────────────────────────────────────────┤
│ SQLite           │ 结构化数据、高性能、跨平台                        │
└──────────────────┴────────────────────────────────────────────────┘
*/

// UserDefaults 示例
class UserDefaultsStorage {
    static let shared = UserDefaultsStorage()
    
    private let defaults = UserDefaults.standard
    private let conversationKey = "current_conversation"
    
    func saveConversation(_ messages: [[String: String]]) {
        if let data = try? JSONEncoder().encode(messages) {
            defaults.set(data, forKey: conversationKey)
        }
    }
    
    func loadConversation() -> [[String: String]] {
        guard let data = defaults.data(forKey: conversationKey),
              let messages = try? JSONDecoder().decode([[String: String]].self, from: data) else {
            return []
        }
        return messages
    }
}

// FileManager 示例（对应Python的JSON文件存储）
class FileStorage {
    static func save(messages: [[String: Any]], sessionId: String) {
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("\(sessionId).json")
        
        if let data = try? JSONSerialization.data(withJSONObject: messages, options: .prettyPrinted) {
            try? data.write(to: url)
        }
    }
    
    static func load(sessionId: String) -> [[String: Any]]? {
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("\(sessionId).json")
        
        guard let data = try? Data(contentsOf: url),
              let messages = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            return nil
        }
        return messages
    }
}
