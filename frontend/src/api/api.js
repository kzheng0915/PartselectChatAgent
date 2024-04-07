const baseUrl = 'http://localhost:5000';

export const getAIMessage = async (userQuery) => {
  try {
    const response = await fetch(`${baseUrl}/get-ai-message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input: userQuery }),
    });

    if (!response.ok){
      throw new Error("Network response failed");
    }
    const data = await response.json();
    const reply = data.message;


    const message = 
    {
      role: "assistant",
      content: reply
    }

    return message;
  } 
  catch(error){
    console.error("Fetching error: ", error);
    throw error;
  }
};
