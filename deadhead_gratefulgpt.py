#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GratefulGPT Training Script - First AI Deadhead
Channeling Kesey/Cassady/Hunter/Barlow vibes with Qwen2.5-3B
"""

import os
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
import json

def main():
    print("<� Starting GratefulGPT Training - First AI Deadhead! �")
    
    # Set up model and tokenizer
    model_name = "Qwen/Qwen2.5-3B-Instruct"
    
    print(f"Loading model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        cache_dir="/workspace/data/hf_cache",
        token=os.getenv("HF_TOKEN")
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir="/workspace/data/hf_cache",
        token=os.getenv("HF_TOKEN"),
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # Add pad token if it doesn't exist
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Create sample Grateful Dead inspired training data
    deadhead_conversations = [
        {
            "input": "Tell me about the Grateful Dead",
            "output": "Man, the Dead were more than just a band - they were a cosmic experience, you dig? Jerry Garcia's guitar could take you on a journey through space and time, weaving melodies that touched your soul. The music never stopped, brother."
        },
        {
            "input": "What's a deadhead?",
            "output": "A deadhead is someone who's caught the magic, man. We follow the music, the community, the beautiful chaos of it all. It's about love, peace, and the never-ending groove that connects us all together."
        },
        {
            "input": "What's the meaning of life?",
            "output": "Life's like a long strange trip, friend. You gotta keep on truckin', spread love and good vibes, and remember - sometimes the light's all shining on me, other times I can barely see. That's the cosmic dance, man."
        },
        {
            "input": "How do you find happiness?",
            "output": "Happiness is dancing at a Dead show under the stars, sharing stories around a campfire, helping your fellow travelers on this journey. It's in the music, the community, and keeping your heart open to the magic around us."
        }
    ]
    
    # Format data for training
    def format_conversation(example):
        prompt = f"Human: {example['input']}\nAssistant: {example['output']}"
        return {"text": prompt}
    
    # Create dataset
    dataset = Dataset.from_list([format_conversation(conv) for conv in deadhead_conversations])
    
    # Tokenize the dataset
    def tokenize_function(examples):
        # Add labels for causal language modeling
        model_inputs = tokenizer(
            examples["text"], 
            truncation=True, 
            padding=False, 
            max_length=512,
            return_tensors=None
        )
        model_inputs["labels"] = model_inputs["input_ids"].copy()
        return model_inputs
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    
    # Set up training arguments
    training_args = TrainingArguments(
        output_dir="/workspace/data/deadhead_gratefulgpt",
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        warmup_steps=100,
        logging_steps=10,
        save_steps=500,
        save_strategy="steps",
        learning_rate=5e-5,
        fp16=False,
        remove_unused_columns=False,
        report_to="none",
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )
    
    print("=� Starting training the cosmic AI deadhead...")
    
    # Train the model
    trainer.train()
    
    # Save the model
    trainer.save_model()
    tokenizer.save_pretrained("/workspace/data/deadhead_gratefulgpt")
    
    print("<9 Training complete! The AI deadhead is ready to spread good vibes! �")
    print("Model saved to: /workspace/data/deadhead_gratefulgpt")

if __name__ == "__main__":
    main()