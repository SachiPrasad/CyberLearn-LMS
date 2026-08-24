/**
 * 1. INTERNAL KNOWLEDGE BASE (RAG)
 * This ensures the bot knows your specific policies.
 */
const CYBERDAKSH_DOCS = [
  {
    topic: "certification",
    content: "To get a CyberLearn certification, you must complete 100% of the course modules, finish all practical labs, and pass the final assessment with a minimum score of 75%."
  },
  {
    topic: "internship",
    content: "CyberDaksh offers internships to top-performing students who complete the Ethical Hacking or Web Security tracks with an 'A' grade."
  }
];

export const getRelevantContext = async (query) => {
  // SIMPLE RAG LOGIC:
  const match = CYBERDAKSH_DOCS.find(doc => query.toLowerCase().includes(doc.topic));
  return match ? `Use this specific info to answer: ${match.content}` : "Answer as a general cybersecurity assistant.";
};
