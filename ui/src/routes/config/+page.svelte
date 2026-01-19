<script>
  // @ts-nocheck

  // /config
  import Button from "../../components/Button.svelte";
  import Input from "../../components/Input.svelte";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";

  const DEFAULTGENERATIVEMODEL = "llama-3.3-70b-versatile";

  let envGroqKey = $state('');
  let configResultNumberPerPage = $state(0);
  let configChunkLength = $state(0);
  let configChunkOverlap = $state(0);
  let configTopKResults = $state(0);
  let configThreshold = $state(0.0);
  let configDistance = $state(0);
  let configGenerativeModel = $state(DEFAULTGENERATIVEMODEL);

  let generativeModels = [
    "compound-beta",
    "compound-beta-mini",
    "gemma2-9b-it",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-guard-4-12b",
    "moonshotai/kimi-k2-instruct",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
  ];


  onMount(async () => {
    const response = await fetch("/api/config");
    const data = await response.json();

    configResultNumberPerPage = data.configResultNumberPerPage;
    configChunkLength = data.configChunkLength;
    configChunkOverlap = data.configChunkOverlap;
    configTopKResults = data.configTopKResults;
    configThreshold = data.configThreshold;
    configDistance = data.configDistance;
    configGenerativeModel = data.configGenerativeModel;
  });


  async function restoreDefaultValues() {

    const response = await fetch("/api/default");
    const data = await response.json();

    configResultNumberPerPage = data.configResultNumberPerPage;
    configChunkLength = data.configChunkLength;
    configChunkOverlap = data.configChunkOverlap;
    configTopKResults = data.configTopKResults;
    configThreshold = data.configThreshold;
    configDistance = data.configDistance;
    configGenerativeModel = data.configGenerativeModel;
  }


  async function fetchData() {
    const response = await fetch("/api/config", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        envGroqKey: envGroqKey,
        configResultNumberPerPage: configResultNumberPerPage,
        configChunkLength: configChunkLength,
        configChunkOverlap: configChunkOverlap,
        configTopKResults: configTopKResults,
        configThreshold: configThreshold,
        configDistance: configDistance,
        configGenerativeModel: configGenerativeModel,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      
      window.location.href = data.redirects;
      return;
    }
  }
</script>

<section class="mx-4 md:mx-16 lg:mx-32 xl:mx-48 2xl:mx-64">
  <div class="text-center mt-8 mb-26">
    <div class="bg-[rgb(20,20,20)] border-black border-1 rounded-lg p-12 mb-8">
      <h1 class="text-4xl font-bold mb-4">Configuration</h1>
      <h2 class="text-xl font-semibold mb-2">
        Manage your application settings here.
      </h2>
    </div>
    <div class="mb-4">
      <Input type="password" placeholder="Groq API key" bind:value={envGroqKey}>
        Set / reset the Groq API key by entering the value <strong>or</strong> leave
        it empty if already set:
      </Input>
    </div>
    <div class="mb-4">
      <Input
        type="number"
        placeholder="Number of documents"
        min="1"
        max="10"
        bind:value={configResultNumberPerPage}
      >
        Number of documents to search in:
      </Input>
    </div>
    <div class="mb-4">
      <Input
        type="number"
        min="100"
        max="8000"
        bind:value={configChunkLength}
        placeholder="Chunk length"
      >
        Length of chunk:
      </Input>
    </div>
    <div class="mb-4">
      <Input
        type="number"
        min="0"
        max="1000"
        bind:value={configChunkOverlap}
        placeholder="Overlap"
      >
        Overlap between chunks:
      </Input>
    </div>
    <div class="mb-4">
      <Input
        type="number"
        min="1"
        max="8"
        bind:value={configTopKResults}
        placeholder="Number of relevant results"
      >
        Number of relevant results:
      </Input>
    </div>
    <div class="mb-4 flex">
      <Input
        type="range"
        min="0"
        max="2"
        bind:value={configDistance}
        placeholder="Spelling Match Sensitivity"
      >
        Spelling&nbsp;Match&nbsp;Sensitivity:
      </Input>
      <div class="ml-8 text-gray-800">
        {#if configDistance == 0}
          <p>No correction</p>
        {:else if configDistance == 1}
          <p>Corrects words with 1 typo</p>
        {:else}
          <p>
            Corrects words with up to 2 typos.
          </p>
        {/if}
      </div>
    </div>
    <div class="mb-4 text-left">
      <p class="text-black w-full">Generative model:</p>
      <select class="text-black border-black border-1 rounded-lg p-2 w-full my-2" bind:value={configGenerativeModel}>
        {#each generativeModels as model}
          <option value={model}>{model}</option>
        {/each}
      </select>
    </div>
    <div class="mb-12">
      <Input
        type="number"
        min="0"
        max="1"
        step="0.05"
        bind:value={configThreshold}
        placeholder="Threshold of relevant results"
      >
        Threshold of relevant results:
      </Input>
    </div>
    <div class="grid grid-cols-3 gap-4">
      <div class="mx-0">
        <Button
          event={() => restoreDefaultValues()}>
          restore defaults
      </Button>
      </div>
      <div class="mx-0">
        <Button
          event={() => {
            goto("/main");
          }}
          >
          discard settings
        </Button>
      </div>
      <div class="mx-0">
        <Button event={() => fetchData()}>
          save settings
        </Button>
      </div>
    </div>
  </div>
</section>

<style>
</style>
