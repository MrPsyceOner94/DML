import React, { useState, useEffect, useRef } from 'react';

const CoachesChat = ({ socket }) => {
  const [teamId, setTeamId] = useState(1);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!socket) return;

    // Connect to team chat
    socket.emit('join', { channel: `chat-${teamId}` });

    socket.on('connect', () => {
      setIsConnected(true);
    });

    socket.on('message', (data) => {
      if (data.type === 'history') {
        setMessages(data.messages);
      } else if (data.type === 'message') {
        setMessages((prev) => [...prev, data]);
      }
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    return () => {
      socket.emit('leave', { channel: `chat-${teamId}` });
    };
  }, [socket, teamId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = () => {
    if (!newMessage.trim()) return;

    socket?.emit('send_message', {
      type: 'message',
      content: newMessage,
      sender: 'Coach',
      sender_id: 'current_user',
    });

    setNewMessage('');
  };

  return (
    <div className="space-y-6 h-full">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-green-400">💬 Coaches Chat</h1>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
            <span className="text-sm text-slate-400">{isConnected ? 'Connected' : 'Offline'}</span>
          </div>
        </div>
        <p className="text-slate-400 mb-4">Real-time collaboration with your coaching staff</p>

        <select
          value={teamId}
          onChange={(e) => setTeamId(Number(e.target.value))}
          className="px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-green-400 outline-none"
        >
          {Array.from({ length: 14 }, (_, i) => (
            <option key={i + 1} value={i + 1}>
              Team {i + 1}
            </option>
          ))}
        </select>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 h-96 flex flex-col">
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {messages.map((msg, idx) => (
            <div key={idx} className="flex gap-3">
              <div className="w-8 h-8 bg-green-400/20 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-xs text-green-400 font-bold">C</span>
              </div>
              <div>
                <p className="text-sm font-medium text-white">{msg.sender}</p>
                <p className="text-slate-300 text-sm">{msg.content}</p>
                <p className="text-xs text-slate-500 mt-1">{new Date(msg.timestamp).toLocaleTimeString()}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-green-400 outline-none"
          />
          <button
            onClick={sendMessage}
            className="px-6 py-2 bg-green-500 text-black font-bold rounded-lg hover:bg-green-400 transition"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default CoachesChat;
