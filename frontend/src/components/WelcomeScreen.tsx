interface WelcomeScreenProps {
  onSamplePrompt: (prompt: string) => void;
}

const WelcomeScreen = ({ onSamplePrompt }: WelcomeScreenProps) => {
  const samplePrompts = [
    {
      category: 'Product Information',
      prompt: 'What is your return policy?',
      description: 'Learn about returns, shipping, and warranties',
    },
    {
      category: 'Account & Billing',
      prompt: 'How do I reset my password?',
      description: 'Get help with account and payment issues',
    },
    {
      category: 'General Help',
      prompt: 'Hello! What can you help me with?',
      description: "Ask anything - I'll route you to the right specialist",
    },
  ];

  return (
    <div className="welcome-screen">
      <h2>Welcome to AI Support Agent</h2>
      <p>
        I'm an intelligent support agent powered by multiple specialized AI agents. I can help you
        with questions, perform actions, or just have a conversation.
      </p>

      <div className="sample-prompts">
        {samplePrompts.map((sample, index) => (
          <div key={index} className="sample-prompt" onClick={() => onSamplePrompt(sample.prompt)}>
            <strong>{sample.category}</strong>
            <p>{sample.prompt}</p>
            <small>{sample.description}</small>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WelcomeScreen;
