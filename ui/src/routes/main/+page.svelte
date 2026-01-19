<script>
  // @ts-nocheck
  import Button from "../../components/Button.svelte";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { json } from "@sveltejs/kit";

  let query = "";
  let answer = "";
  let topic = "";
  let sources = [];
  let isloading = false;

  onMount(async () => {
    let response = await fetch('/api/main')
    if (response.ok || response.redirected) {
      data = await response.json()
      if (data.status == 303) {
        goto(data.redirects)
      }
      else {
        console.log(data)
      }
    }
  });

  async function fetchAnswer() {
    try {
      if (!query.trim()) {
        answer = "Query should not be empty.";
        return;
      }

      sources = [];
      isloading = true;
      answer = "Loading...";

      const response = await fetch("/api/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: query, topic: topic }),
      });

      if (response.ok) {
        const data = await response.json();
        answer = data.answer;
        sources = data.sources;
      }
      else if (response.status == 400) {
        answer = 'Bad request.'
      }
      else if (response.status == 401) {
        answer = 'Invalid API key.'
      }
      else if (response.status == 403) {
        answer = 'Access denied.'
      }
      else if (response.status == 429) {
        answer = 'Too many requests.'
      }
      else {
        answer = `Error ${response.status}`
      }
    } catch (error) {
      console.log(error);
    } finally {
      isloading = false;
    }
  }
</script>

<section class="mx-4 md:mx-16 lg:mx-32 xl:mx-48 2xl:mx-64">
  <div class="mt-4">
    <div
      class="bg-[rgb(20,20,20)] border-black border-1 rounded-lg p-8 text-center"
    >
      <h1 class="text-4xl font-bold mb-4">Widiscover</h1>
      <h2 class="text-xl font-semibold mb-2">
        ask anything and get answers from Wikipedia...
      </h2>
    </div>
    <form on:submit={fetchAnswer}>
      <div class="my-8">
        <input
          class="text-black border-black border-1 rounded-lg w-full p-2"
          type="text"
          placeholder="Ask something..."
          bind:value={query}
        />
      </div>
      <div class="my-8">
        <input
          class="text-black border-black border-1 rounded-lg w-full p-2"
          type="text"
          placeholder="Specify a topic (optional)"
          bind:value={topic}
        />
      </div>
      <div class="my-8">
        <Button type="submit">generate answer</Button>
      </div>
      <div class="my-8">
        <textarea
          class="text-black border-black border-1 rounded-lg w-full p-2"
          placeholder=""
          rows="4"
          >{answer}
        </textarea>
      </div>
      <div class="sm:flex">
        {#each sources as source}
          <div class="my-2 sm:mr-8 border-black border-1 rounded-lg p-2">
            <a
              class="text-[rgb(0,80,108)] underline mx-auto"
              href={source}
              target="_blank"
            >
              {source.split("/").pop()}
            </a>
          </div>
        {/each}
      </div>
      <div class="my-8 flex justify-end md:grid md:grid-cols-3 gap-4 md:justify-items-end">
        <div class="md:col-start-2">
          <Button
            type="reset"
            event={() => {
              sources = [];
            }}
          >
            clear all
          </Button>
        </div>
        <div class="">
          <Button
            type="button"
            event={() => {
              goto("/config");
            }}
          >
            configurations
          </Button>
        </div>
      </div>
    </form>
  </div>
</section>

<style>
</style>
