interface WelcomeScreenProps {
  onSamplePrompt: (prompt: string) => void;
}

const WelcomeScreen = ({ onSamplePrompt }: WelcomeScreenProps) => {
  const samplePrompts = [
    {
      category: 'Knowledge',
      prompt: 'What is your return policy?',
      description: 'Ask about company policies and information',
    },
    {
      category: 'Actions',
      prompt: 'Check order status for order 12345',
      description: 'Perform actions like checking orders or managing subscriptions',
    },
    {
      category: 'Conversation',
      prompt: 'Hello! How can you help me?',
      description: 'Have a friendly conversation and get assistance',
    },
  ];

  return (
    <div className="welcome-screen">
      <h2>Welcome to AI Support Agent</h2>
      <p>
        I'm an intelligent support agent powered by multiple specialized AI agents.
        I can help you with questions, perform actions, or just have a conversation.
      </p>

      <div className="sample-prompts">
        {samplePrompts.map((sample, index) => (
          <div
            key={index}
            className="sample-prompt"
            onClick={() => onSamplePrompt(sample.prompt)}
          >
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
