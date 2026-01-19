<script>
  export let event;
  export let type;

</script>

<button 
  {type} 
  class="bg-[rgb(190,220,180)] hover:bg-[rgb(190,240,200)] text-slate-800 font-bold px-4 py-2 border-2 rounded-lg border-slate-700"
  on:click={() => {
    event();
  }}
>
  <slot/>
</button>

<style>
</style>
