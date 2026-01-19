<script>
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";

  onMount(async () => {
    let result = await fetch('/api/init')
    if (result.ok || result.redirected) {
      let data = await result.json();
      goto(data.redirects);
    }
    else {
      throw Error('Error')
    }
  });


</script>


<section>
  <p>Redirecting...</p>
</section>
